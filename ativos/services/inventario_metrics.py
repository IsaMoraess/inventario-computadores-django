import re
import unicodedata
from collections import Counter

from django.db.models import Count, Q


PENDENCIA_TERMOS = (
    'nao informado',
    'nao informado',
    'ninguem',
    'ninguem',
    'sem usuario',
    'sem usuario',
)

PENDENCIA_CAMPOS = (
    'usuario',
    'sistema',
    'ram',
    'processador',
    'armazenamento',
)


def normalizar(valor):
    valor = (valor or '').strip().lower()
    return ''.join(
        char
        for char in unicodedata.normalize('NFKD', valor)
        if not unicodedata.combining(char)
    )


def rotulo(valor, fallback='Nao informado'):
    valor = (valor or '').strip()
    return valor if valor else fallback


def pendencias_q():
    query = Q()

    for campo in PENDENCIA_CAMPOS:
        query |= Q(**{f'{campo}__isnull': True})
        query |= Q(**{campo: ''})
        for termo in PENDENCIA_TERMOS:
            query |= Q(**{f'{campo}__iexact': termo})
            query |= Q(**{f'{campo}__icontains': termo})

    return query


def motivos_pendencia(computador):
    motivos = []

    for campo in PENDENCIA_CAMPOS:
        valor = getattr(computador, campo, '')
        normalizado = normalizar(valor)
        nome_campo = campo.replace('_', ' ').title()

        if not normalizado:
            motivos.append(f'{nome_campo} vazio')
        elif any(normalizar(termo) in normalizado for termo in PENDENCIA_TERMOS):
            motivos.append(f'{nome_campo}: {rotulo(valor)}')

    return motivos


def contar_status(computadores):
    contagem = Counter()

    for status in computadores.values_list('status', flat=True):
        normalizado = normalizar(status)

        if normalizado.startswith('ativo'):
            contagem['ativos'] += 1
        elif 'manuten' in normalizado:
            contagem['manutencao'] += 1
        elif 'desligado' in normalizado:
            contagem['desligados'] += 1
        elif 'reserva' in normalizado:
            contagem['reservas'] += 1

    return contagem


def status_css_class(status):
    normalizado = normalizar(status)

    if 'manuten' in normalizado:
        return 'status-manutencao'
    if 'reserva' in normalizado:
        return 'status-reserva'
    if 'desligado' in normalizado:
        return 'status-desligado'
    return 'status-ativo'


def contar_windows(computadores):
    contagem = Counter({'Windows 10': 0, 'Windows 11': 0, 'Outros / Nao informado': 0})

    for sistema in computadores.values_list('sistema', flat=True):
        normalizado = normalizar(sistema)

        if 'windows 11' in normalizado or normalizado == 'win11':
            contagem['Windows 11'] += 1
        elif 'windows 10' in normalizado or normalizado == 'win10':
            contagem['Windows 10'] += 1
        else:
            contagem['Outros / Nao informado'] += 1

    return contagem


def grafico_por_campo(computadores, campo, fallback='Nao informado', limite=None, ordenar_por_total=True):
    ordenacao = ['-total', campo] if ordenar_por_total else [campo]
    grupos = computadores.values(campo).annotate(total=Count('id')).order_by(*ordenacao)

    if limite:
        grupos = grupos[:limite]

    dados = []
    for item in grupos:
        valor = item[campo]
        ids = list(
            computadores.filter(**{campo: valor})
            .order_by('id')
            .values_list('id', flat=True)
        )
        dados.append(
            {
                'label': rotulo(valor, fallback),
                'value': item['total'],
                'ids': ids,
            }
        )

    return dados


def grafico_windows(computadores):
    grupos = {
        'Windows 10': [],
        'Windows 11': [],
        'Outros / Nao informado': [],
    }

    for computador in computadores.only('id', 'sistema').order_by('id'):
        normalizado = normalizar(computador.sistema)

        if 'windows 11' in normalizado or normalizado == 'win11':
            grupos['Windows 11'].append(computador.id)
        elif 'windows 10' in normalizado or normalizado == 'win10':
            grupos['Windows 10'].append(computador.id)
        else:
            grupos['Outros / Nao informado'].append(computador.id)

    return [
        {
            'label': label,
            'value': len(ids),
            'ids': ids,
        }
        for label, ids in grupos.items()
    ]


def ram_gb(computador):
    match = re.search(r'\d+', str(getattr(computador, 'ram', '') or ''))
    return int(match.group(0)) if match else None


def tem_pouca_ram(computador, limite_gb=4):
    ram = ram_gb(computador)
    return ram is not None and ram <= limite_gb


def motivos_alerta(computador):
    motivos = []
    status = normalizar(computador.status)

    if 'manuten' in status:
        motivos.append('Em manutencao')
    if 'desligado' in status:
        motivos.append('Desligado')
    if tem_pouca_ram(computador):
        motivos.append('Pouca RAM')

    pendencias = motivos_pendencia(computador)
    if pendencias:
        motivos.append('Dados pendentes')

    usuario = normalizar(computador.usuario)
    if not usuario or 'sem usuario' in usuario or 'ninguem' in usuario:
        motivos.append('Sem usuario')

    return list(dict.fromkeys(motivos))


def computadores_com_alerta(computadores):
    return [
        {
            'computador': computador,
            'motivos': motivos,
        }
        for computador in computadores.order_by('sala', 'id')
        for motivos in [motivos_alerta(computador)]
        if motivos
    ]
