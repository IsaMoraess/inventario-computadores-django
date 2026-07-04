from django.apps import AppConfig


class AtivosConfig(AppConfig):
    name = 'ativos'

    def ready(self):
        import ativos.signals  # noqa: F401
