import json
import logging

from django.core.cache import cache
from django.db import connection, transaction

from ativos.models import Computador, Movimentacao


logger = logging.getLogger(__name__)

FONTE_OFICIAL = 'public.computadores'

ID_RENAMES = {
    'ASUS': 'SUP02',
    'Notebook HP 256R': 'SUP01',
    'PC-35': 'JUR01',
    'PC-36': 'REU01',
}

NEW_TO_OLD = {new_id: old_id for old_id, new_id in ID_RENAMES.items()}

FIELDS = [
    'id',
    'sala',
    'x',
    'y',
    'status',
    'armazenamento',
    'placa_video',
    'usuario',
    'sistema',
    'ram',
    'processador',
    'observacoes',
]

TEXT_FIELDS = [
    'sala',
    'armazenamento',
    'placa_video',
    'usuario',
    'sistema',
    'ram',
    'processador',
    'observacoes',
]


def sincronizar_computadores_supabase():
    registros = fetch_computadores_oficiais()
    ids_oficiais = {
        clean_value(registro.get('id'))
        for registro in registros
        if clean_value(registro.get('id'))
    }
    ids_processados = set()
    resultado = {
        'criados': 0,
        'atualizados': 0,
        'removidos': 0,
        'ignorados': 0,
        'erros': 0,
        'avisos': [],
    }

    with transaction.atomic():
        for row_number, registro in enumerate(registros, start=1):
            computador_id = clean_value(registro.get('id'))

            if not computador_id:
                resultado['ignorados'] += 1
                resultado['avisos'].append(
                    f'Registro {row_number} ignorado: campo id vazio.'
                )
                continue

            if computador_id in ids_processados:
                resultado['ignorados'] += 1
                resultado['avisos'].append(
                    f'Registro {row_number} ignorado: ID {computador_id} duplicado na fonte oficial.'
                )
                continue

            new_id = ID_RENAMES.get(computador_id)
            if new_id and new_id in ids_oficiais:
                resultado['ignorados'] += 1
                resultado['avisos'].append(
                    f'{computador_id} ignorado: ID antigo substituido por {new_id}.'
                )
                continue

            ids_processados.add(computador_id)
            dados = build_computer_data(registro, row_number, resultado['avisos'])
            old_id = NEW_TO_OLD.get(computador_id)
            computador = Computador.objects.filter(pk=computador_id).first()
            computador_antigo = (
                Computador.objects.filter(pk=old_id).first()
                if old_id else None
            )

            if computador:
                update_computador(computador, dados)
                resultado['atualizados'] += 1
                valor_anterior = 'Atualizado via Supabase'
            else:
                computador = Computador.objects.create(id=computador_id, **dados)
                resultado['criados'] += 1
                valor_anterior = 'Criado via Supabase'

            if computador_antigo:
                migrar_referencias_computador(
                    antigo=computador_antigo,
                    novo=computador,
                )
                computador_antigo.delete()
                resultado['removidos'] += 1
                resultado['avisos'].append(
                    f'{old_id} -> {computador_id}: antigo removido apos sincronizacao.'
                )

            registrar_movimentacao(
                computador=computador,
                dados=dados,
                valor_anterior=valor_anterior,
            )

    cache.clear()
    return resultado


def corrigir_ids_duplicados(confirmar=False):
    registros_oficiais = {
        clean_value(registro.get('id')): registro
        for registro in fetch_computadores_oficiais()
    }
    resultado = {
        'criados': 0,
        'atualizados': 0,
        'removidos': 0,
        'ignorados': 0,
        'avisos': [],
        'confirmado': confirmar,
    }

    with transaction.atomic():
        for old_id, new_id in ID_RENAMES.items():
            computador_antigo = Computador.objects.filter(pk=old_id).first()
            computador_novo = Computador.objects.filter(pk=new_id).first()
            registro_oficial = registros_oficiais.get(new_id)

            if not computador_antigo:
                resultado['ignorados'] += 1
                resultado['avisos'].append(
                    f'{old_id} -> {new_id}: antigo nao encontrado.'
                )
                continue

            if not registro_oficial and not computador_novo:
                resultado['ignorados'] += 1
                resultado['avisos'].append(
                    f'{old_id} -> {new_id}: novo ID nao existe em {FONTE_OFICIAL}.'
                )
                continue

            resultado['avisos'].append(
                f'{old_id} -> {new_id}: '
                f'{"sera corrigido" if confirmar else "seria corrigido"}.'
            )

            if not confirmar:
                continue

            if registro_oficial:
                dados = build_computer_data(registro_oficial, 0, resultado['avisos'])
                if computador_novo:
                    update_computador(computador_novo, dados)
                    resultado['atualizados'] += 1
                else:
                    computador_novo = Computador.objects.create(id=new_id, **dados)
                    resultado['criados'] += 1

            migrar_referencias_computador(
                antigo=computador_antigo,
                novo=computador_novo,
            )
            computador_antigo.delete()
            resultado['removidos'] += 1

            registrar_movimentacao(
                computador=computador_novo,
                dados={'id_anterior': old_id, 'id_novo': new_id},
                valor_anterior=f'ID anterior: {old_id}',
            )

    if confirmar:
        cache.clear()

    return resultado


def fetch_computadores_oficiais():
    columns = ', '.join(FIELDS)
    query = f'SELECT {columns} FROM {FONTE_OFICIAL}'

    with connection.cursor() as cursor:
        cursor.execute(query)
        column_names = [column[0] for column in cursor.description]
        return [
            dict(zip(column_names, row))
            for row in cursor.fetchall()
        ]


def atualizar_posicao_supabase(computador_id, x, y):
    if connection.vendor != 'postgresql':
        # Sem base compartilhada com o Supabase (ex.: ambiente local em sqlite),
        # nao ha nada para sincronizar e nao ha o que reportar como falha.
        return True

    ids_candidatos = [computador_id]
    old_id = NEW_TO_OLD.get(computador_id)
    if old_id:
        ids_candidatos.append(old_id)

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f'UPDATE {FONTE_OFICIAL} SET x = %s, y = %s WHERE id = ANY(%s)',
                [x, y, ids_candidatos],
            )
            return cursor.rowcount > 0
    except Exception:
        logger.exception(
            'Falha ao sincronizar posicao do computador %s com o Supabase.',
            computador_id,
        )
        return False


def build_computer_data(registro, row_number, avisos):
    dados = {
        field: clean_value(registro.get(field))
        for field in TEXT_FIELDS
    }
    dados['x'] = parse_int(registro.get('x'), row_number, 'x', avisos)
    dados['y'] = parse_int(registro.get('y'), row_number, 'y', avisos)
    dados['status'] = normalize_status(registro.get('status'), row_number, avisos)
    return dados


def update_computador(computador, dados):
    for field, value in dados.items():
        setattr(computador, field, value)
    computador.save(update_fields=[*dados.keys(), 'atualizado_em'])


def migrar_referencias_computador(antigo, novo):
    if not novo:
        return

    Movimentacao.objects.filter(computador=antigo).update(
        computador=novo,
        computador_identificador=novo.pk,
    )
    Movimentacao.objects.filter(computador_identificador=antigo.pk).update(
        computador_identificador=novo.pk,
    )


def registrar_movimentacao(computador, dados, valor_anterior):
    Movimentacao.objects.create(
        computador=computador,
        computador_identificador=computador.pk,
        campo='registro',
        valor_anterior=valor_anterior,
        valor_novo=json.dumps(dados, ensure_ascii=False, sort_keys=True),
        acao='Importação Supabase',
        tipo_acao='importacao_supabase',
        descricao=f'Dados sincronizados a partir de {FONTE_OFICIAL}.',
    )


def clean_value(value):
    if value is None:
        return ''
    return str(value).strip()


def parse_int(value, row_number, field_name, avisos):
    value = clean_value(value)
    if not value:
        return 0

    try:
        return int(value)
    except ValueError:
        avisos.append(
            f'Registro {row_number}: campo {field_name} invalido, usando 0.'
        )
        return 0


def normalize_status(value, row_number, avisos):
    status = clean_value(value) or Computador.Status.ATIVO
    valid_statuses = {choice[0] for choice in Computador.Status.choices}

    if status not in valid_statuses:
        avisos.append(
            f'Registro {row_number}: status "{status}" invalido, usando Ativo.'
        )
        return Computador.Status.ATIVO

    return status
