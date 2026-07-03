import json

from django.core.management.base import BaseCommand, CommandError
from django.db import connection, transaction

from ativos.models import Computador, Movimentacao


class Command(BaseCommand):
    help = 'Importa computadores diretamente da tabela public.computadores.'

    fields = [
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

    text_fields = [
        'sala',
        'armazenamento',
        'placa_video',
        'usuario',
        'sistema',
        'ram',
        'processador',
        'observacoes',
    ]

    def handle(self, *args, **options):
        criados = 0
        atualizados = 0

        try:
            registros = self.fetch_supabase_records()
        except Exception as error:
            raise CommandError(
                f'Erro ao ler public.computadores: {type(error).__name__}: {error}'
            ) from error

        with transaction.atomic():
            for row_number, registro in enumerate(registros, start=1):
                computador_id = self.clean_value(registro.get('id'))

                if not computador_id:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Registro {row_number} ignorado: campo id vazio.'
                        )
                    )
                    continue

                dados = self.build_computer_data(registro, row_number)
                computador, created = Computador.objects.update_or_create(
                    id=computador_id,
                    defaults=dados,
                )

                if created:
                    criados += 1
                    valor_anterior = ''
                else:
                    atualizados += 1
                    valor_anterior = 'Atualizado via Supabase'

                Movimentacao.objects.create(
                    computador=computador,
                    campo='registro',
                    valor_anterior=valor_anterior,
                    valor_novo=self.serialize_values(dados),
                    acao='Importação Supabase',
                )

        self.stdout.write(self.style.SUCCESS('Importacao Supabase concluida.'))
        self.stdout.write(f'Criados: {criados}')
        self.stdout.write(f'Atualizados: {atualizados}')

    def fetch_supabase_records(self):
        columns = ', '.join(self.fields)
        query = f'SELECT {columns} FROM public.computadores'

        with connection.cursor() as cursor:
            cursor.execute(query)
            column_names = [column[0] for column in cursor.description]
            return [
                dict(zip(column_names, row))
                for row in cursor.fetchall()
            ]

    def build_computer_data(self, registro, row_number):
        dados = {
            field: self.clean_value(registro.get(field))
            for field in self.text_fields
        }
        dados['x'] = self.parse_int(registro.get('x'), row_number, 'x')
        dados['y'] = self.parse_int(registro.get('y'), row_number, 'y')
        dados['status'] = self.normalize_status(registro.get('status'), row_number)
        return dados

    def clean_value(self, value):
        if value is None:
            return ''
        return str(value).strip()

    def parse_int(self, value, row_number, field_name):
        value = self.clean_value(value)
        if not value:
            return 0

        try:
            return int(value)
        except ValueError:
            self.stdout.write(
                self.style.WARNING(
                    f'Registro {row_number}: campo {field_name} invalido, usando 0.'
                )
            )
            return 0

    def normalize_status(self, value, row_number):
        status = self.clean_value(value) or Computador.Status.ATIVO
        valid_statuses = {choice[0] for choice in Computador.Status.choices}

        if status not in valid_statuses:
            self.stdout.write(
                self.style.WARNING(
                    f'Registro {row_number}: status "{status}" invalido, usando Ativo.'
                )
            )
            return Computador.Status.ATIVO

        return status

    def serialize_values(self, values):
        return json.dumps(values, ensure_ascii=False, sort_keys=True)
