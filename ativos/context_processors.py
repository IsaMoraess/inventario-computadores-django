from django.templatetags.static import static

from .services.configuracao_service import get_config


def _logo_url(config):
    if config.logo:
        try:
            if config.logo.storage.exists(config.logo.name):
                return config.logo.url
        except Exception:
            pass

    return static('img/logo_jr.png')


def sistema_config(request):
    config = get_config()
    return {
        'sistema_config': config,
        'sistema_logo_url': _logo_url(config),
    }
