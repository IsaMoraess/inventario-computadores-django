import django.db.models.deletion
from django.db import migrations, models


def preencher_identificador(apps, schema_editor):
    Movimentacao = apps.get_model('ativos', 'Movimentacao')

    for movimentacao in Movimentacao.objects.exclude(computador_id__isnull=True):
        movimentacao.computador_identificador = movimentacao.computador_id
        movimentacao.save(update_fields=['computador_identificador'])


class Migration(migrations.Migration):

    dependencies = [
        ('ativos', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='movimentacao',
            name='computador',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='movimentacoes', to='ativos.computador'),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='computador_identificador',
            field=models.CharField(blank=True, db_index=True, max_length=50),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='tipo_acao',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='descricao',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='movimentacao',
            name='usuario_responsavel',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AlterField(
            model_name='movimentacao',
            name='campo',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.RunPython(preencher_identificador, migrations.RunPython.noop),
    ]
