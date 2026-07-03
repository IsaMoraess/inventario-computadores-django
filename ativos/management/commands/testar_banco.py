from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Testa a conexao com o banco configurado no Django.'

    def handle(self, *args, **options):
        database_settings = connection.settings_dict

        self.stdout.write(f"ENGINE: {database_settings.get('ENGINE')}")
        self.stdout.write(f"NAME: {database_settings.get('NAME')}")
        self.stdout.write(f"HOST: {database_settings.get('HOST')}")
        self.stdout.write(f"PORT: {database_settings.get('PORT')}")
        self.stdout.write(f"USER: {database_settings.get('USER')}")

        try:
            connection.ensure_connection()
            self.stdout.write(self.style.SUCCESS('CONEXAO: abriu com sucesso'))
        except Exception as error:
            self.stdout.write(
                self.style.ERROR(
                    f'CONEXAO: falhou: {type(error).__name__}: {error}'
                )
            )
            return

        checks = [
            ('current_database', 'SELECT current_database()'),
            ('current_schema', 'SELECT current_schema()'),
            ('to_regclass', "SELECT to_regclass('public.computadores')"),
            ('count_computadores', 'SELECT COUNT(*) FROM public.computadores'),
        ]

        with connection.cursor() as cursor:
            for label, query in checks:
                try:
                    cursor.execute(query)
                    value = cursor.fetchone()[0]
                    self.stdout.write(f'{label}: {value}')
                except Exception as error:
                    self.stdout.write(
                        self.style.ERROR(
                            f'{label}: erro: {type(error).__name__}: {error}'
                        )
                    )
