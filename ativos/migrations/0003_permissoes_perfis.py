from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ativos', '0002_movimentacao_historico'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='computador',
            options={
                'ordering': ['sala', 'id'],
                'permissions': [
                    ('can_reposition_computador', 'Pode reposicionar computadores'),
                    ('can_download_qrcodes', 'Pode baixar QR Codes'),
                    ('can_download_reports', 'Pode baixar relatorios'),
                ],
                'verbose_name': 'Computador',
                'verbose_name_plural': 'Computadores',
            },
        ),
        migrations.AlterModelOptions(
            name='planta',
            options={
                'ordering': ['-criada_em'],
                'permissions': [
                    ('can_manage_plantas', 'Pode gerenciar plantas'),
                ],
                'verbose_name': 'Planta',
                'verbose_name_plural': 'Plantas',
            },
        ),
    ]
