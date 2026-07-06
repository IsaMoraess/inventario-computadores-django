from django.core.management.base import BaseCommand, CommandError

from ativos.services.supabase_sync import FONTE_OFICIAL, corrigir_ids_duplicados


class Command(BaseCommand):
    help = 'Corrige IDs duplicados gerados por renomeacoes de computadores.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirmar',
            action='store_true',
            help='Aplica as correcoes. Sem esta opcao, apenas mostra o plano.',
        )

    def handle(self, *args, **options):
        confirmar = options['confirmar']

        try:
            resultado = corrigir_ids_duplicados(confirmar=confirmar)
        except Exception as error:
            raise CommandError(
                f'Erro ao corrigir IDs com base em {FONTE_OFICIAL}: '
                f'{type(error).__name__}: {error}'
            ) from error

        if confirmar:
            self.stdout.write(self.style.SUCCESS('Correcao de IDs aplicada.'))
        else:
            self.stdout.write(
                self.style.WARNING(
                    'Modo simulacao: use --confirmar para aplicar as correcoes.'
                )
            )

        self.stdout.write(f'Fonte oficial: {FONTE_OFICIAL}')
        self.stdout.write(f"Criados: {resultado['criados']}")
        self.stdout.write(f"Atualizados: {resultado['atualizados']}")
        self.stdout.write(f"Removidos: {resultado['removidos']}")
        self.stdout.write(f"Ignorados: {resultado['ignorados']}")

        for aviso in resultado.get('avisos', []):
            self.stdout.write(aviso)
