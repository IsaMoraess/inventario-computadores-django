import json
from io import StringIO

from django.conf import settings
from django.core import serializers
from django.core.cache import cache
from django.core.management import call_command
from django.db import connection
from django.utils import timezone

from ativos.models import Computador, ConfiguracaoSistema, LogSistema, Movimentacao, Planta
from ativos.services.supabase_sync import FONTE_OFICIAL, sincronizar_computadores_supabase


STARTED_AT = timezone.now()


def get_config():
    config = ConfiguracaoSistema.get_solo()
    if not config.app_public_url and settings.APP_PUBLIC_URL:
        config.app_public_url = settings.APP_PUBLIC_URL
        config.save(update_fields=['app_public_url', 'atualizado_em'])
    return config


def app_public_url():
    config_url = (get_config().app_public_url or '').rstrip('/')
    if config_url:
        return config_url
    return (settings.APP_PUBLIC_URL or '').rstrip('/')


def logo_path():
    config = get_config()
    if config.logo and getattr(config.logo, 'path', None):
        try:
            return config.logo.path
        except ValueError:
            return None
    return None


def registrar_log(usuario, acao, resultado):
    username = ''
    if usuario and getattr(usuario, 'is_authenticated', False):
        username = usuario.get_full_name() or usuario.get_username()

    return LogSistema.objects.create(
        usuario=username,
        acao=acao,
        resultado=str(resultado or ''),
    )


def sincronizar_supabase(usuario=None):
    resultado = sincronizar_computadores_supabase()
    criados = resultado['criados']
    atualizados = resultado['atualizados']
    removidos = resultado['removidos']
    ignorados = resultado['ignorados']
    erros = resultado['erros']
    total_processado = criados + atualizados + removidos
    cache.clear()

    config = get_config()
    config.ultima_sincronizacao = timezone.now()
    config.ultima_sincronizacao_total = total_processado
    config.save(update_fields=['ultima_sincronizacao', 'ultima_sincronizacao_total', 'atualizado_em'])

    registrar_log(
        usuario,
        'Sincronizacao Supabase',
        (
            f'Fonte: {FONTE_OFICIAL}; Destino: {Computador._meta.db_table}; '
            f'Criados: {criados}; Atualizados: {atualizados}; '
            f'Removidos: {removidos}; Ignorados: {ignorados}; '
            f'Erros: {erros}; Total processado: {total_processado}'
        ),
    )
    return {
        'criados': criados,
        'atualizados': atualizados,
        'removidos': removidos,
        'ignorados': ignorados,
        'erros': erros,
        'total': total_processado,
        'avisos': resultado.get('avisos', []),
    }


def exportar_banco_json(usuario=None):
    models = [
        *Computador.objects.all(),
        *Planta.objects.all(),
        *Movimentacao.objects.all(),
        get_config(),
    ]
    content = serializers.serialize('json', models, indent=2).encode('utf-8')

    config = get_config()
    config.ultimo_backup = timezone.now()
    config.save(update_fields=['ultimo_backup', 'atualizado_em'])
    registrar_log(usuario, 'Backup exportado', f'{len(models)} registros exportados.')
    return content


def importar_banco_json(file_obj, usuario=None):
    raw = file_obj.read()
    if isinstance(raw, bytes):
        raw = raw.decode('utf-8')

    count = 0
    for obj in serializers.deserialize('json', raw):
        obj.save()
        count += 1

    registrar_log(usuario, 'Backup importado', f'{count} registros importados.')
    return count


def exportar_configuracoes_json(usuario=None):
    config = get_config()
    payload = {
        'nome_empresa': config.nome_empresa,
        'cor_principal': config.cor_principal,
        'cor_secundaria': config.cor_secundaria,
        'cor_cards': config.cor_cards,
        'tema': config.tema,
        'rodape_pdfs': config.rodape_pdfs,
        'app_public_url': config.app_public_url,
        'gerado_em': timezone.localtime(timezone.now()).isoformat(),
    }
    registrar_log(usuario, 'Configuracoes exportadas', 'Arquivo JSON de configuracoes gerado.')
    return json.dumps(payload, ensure_ascii=False, indent=2).encode('utf-8')


def limpar_cache(usuario=None):
    cache.clear()
    registrar_log(usuario, 'Cache limpo', 'Cache do Django limpo com sucesso.')


def banco_conectado():
    try:
        connection.ensure_connection()
        return True
    except Exception:
        return False


def tempo_online():
    delta = timezone.now() - STARTED_AT
    total_seconds = int(delta.total_seconds())
    horas, resto = divmod(total_seconds, 3600)
    minutos, segundos = divmod(resto, 60)
    return f'{horas:02d}h {minutos:02d}m {segundos:02d}s'


def system_check(usuario=None):
    output = StringIO()
    call_command('check', stdout=output)
    texto = output.getvalue().strip() or 'System check identified no issues.'
    registrar_log(usuario, 'Validacao do sistema', texto)
    return texto
