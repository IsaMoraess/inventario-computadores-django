from .services.configuracao_service import get_config


def sistema_config(request):
    return {
        'sistema_config': get_config(),
    }
