import csv
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ativos.models import Computador, Movimentacao


class Command(BaseCommand):
    help = 'Importa computadores a partir de um arquivo CSV.'

    expected_headers = [
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

    def add_arguments(self, parser):
        parser.add_argument('csv_path', type=str, help='Caminho do arquivo CSV a importar.')

    def handle(self, *args, **options):
        csv_path = Path(options['csv_path'])

        if not csv_path.exists():
            raise CommandError(f'Arquivo CSV nao encontrado: {csv_path}')

        criados = 0
        atualizados = 0
        ignorados = 0

        with csv_path.open('r', encoding='utf-8-sig', newline='') as csv_file:
            reader = csv.DictReader(csv_file)
            self.validate_headers(reader.fieldnames)

            with transaction.atomic():
                for line_number, row in enumerate(reader, start=2):
                    if self.is_empty_row(row):
                        ignorados += 1
                        continue

                    computador_id = (row.get('id') or '').strip()
                    if not computador_id:
                        ignorados += 1
                        self.stdout.write(
                            self.style.WARNING(
                                f'Linha {line_number} ignorada: campo id vazio.'
                            )
                        )
                        continue

                    dados = self.build_computer_data(row, line_number)
                    computador, created = Computador.objects.update_or_create(
                        id=computador_id,
                        defaults=dados,
                    )

                    if created:
                        criados += 1
                        self.create_movement(
                            computador=computador,
                            campo='registro',
                            valor_anterior='',
                            valor_novo=self.serialize_values(dados),
                        )
                    else:
                        atualizados += 1
                        self.create_movement(
                            computador=computador,
                            campo='registro',
                            valor_anterior='Atualizado via CSV',
                            valor_novo=self.serialize_values(dados),
                        )

        self.stdout.write(self.style.SUCCESS('Importacao CSV concluida.'))
        self.stdout.write(f'Criados: {criados}')
        self.stdout.write(f'Atualizados: {atualizados}')
        self.stdout.write(f'Ignorados: {ignorados}')

    def validate_headers(self, headers):
        if headers != self.expected_headers:
            found = ','.join(headers or [])
            expected = ','.join(self.expected_headers)
            raise CommandError(
                'Cabecalho CSV invalido.\n'
                f'Esperado: {expected}\n'
                f'Encontrado: {found}'
            )

    def build_computer_data(self, row, line_number):
        dados = {
            field: (row.get(field) or '').strip()
            for field in self.text_fields
        }
        dados['x'] = self.parse_int(row.get('x'), line_number, 'x')
        dados['y'] = self.parse_int(row.get('y'), line_number, 'y')
        dados['status'] = self.normalize_status(row.get('status'), line_number)
        return dados

    def parse_int(self, value, line_number, field_name):
        value = (value or '').strip()
        if not value:
            return 0

        try:
            return int(value)
        except ValueError:
            self.stdout.write(
                self.style.WARNING(
                    f'Linha {line_number}: campo {field_name} invalido, usando 0.'
                )
            )
            return 0

    def normalize_status(self, value, line_number):
        status = (value or '').strip() or Computador.Status.ATIVO
        valid_statuses = {choice[0] for choice in Computador.Status.choices}

        if status not in valid_statuses:
            self.stdout.write(
                self.style.WARNING(
                    f'Linha {line_number}: status "{status}" invalido, usando Ativo.'
                )
            )
            return Computador.Status.ATIVO

        return status

    def create_movement(self, computador, campo, valor_anterior, valor_novo):
        Movimentacao.objects.create(
            computador=computador,
            campo=campo,
            valor_anterior=valor_anterior,
            valor_novo=valor_novo,
            acao='Importação CSV',
        )

    def serialize_values(self, values):
        return json.dumps(values, ensure_ascii=False, sort_keys=True)

    def is_empty_row(self, row):
        return not any((value or '').strip() for value in row.values())
