from django.core.management.base import BaseCommand, CommandError

from ativos.models import Computador
from ativos.services.supabase_sync import (
    FONTE_OFICIAL,
    sincronizar_computadores_supabase,
)


class Command(BaseCommand):
    help = 'Sincroniza computadores usando public.computadores como fonte oficial.'

    def handle(self, *args, **options):
        try:
            resultado = sincronizar_computadores_supabase()
        except Exception as error:
            raise CommandError(
                f'Erro ao sincronizar {FONTE_OFICIAL}: {type(error).__name__}: {error}'
            ) from error

        self.stdout.write(self.style.SUCCESS('Importacao Supabase concluida.'))
        self.stdout.write(f'Fonte: {FONTE_OFICIAL}')
        self.stdout.write(f'Destino: {Computador._meta.db_table}')
        self.stdout.write(f"Criados: {resultado['criados']}")
        self.stdout.write(f"Atualizados: {resultado['atualizados']}")
        self.stdout.write(f"Removidos: {resultado['removidos']}")
        self.stdout.write(f"Ignorados: {resultado['ignorados']}")
        self.stdout.write(f"Erros: {resultado['erros']}")

        for aviso in resultado.get('avisos', []):
            self.stdout.write(self.style.WARNING(aviso))
