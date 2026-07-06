from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ativos', '0003_permissoes_perfis'),
    ]

    operations = [
        migrations.CreateModel(
            name='ConfiguracaoSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_empresa', models.CharField(default='JR Grupo', max_length=120)),
                ('logo', models.ImageField(blank=True, upload_to='configuracoes/')),
                ('cor_principal', models.CharField(default='#38bdf8', max_length=20)),
                ('cor_secundaria', models.CharField(default='#0f2742', max_length=20)),
                ('cor_cards', models.CharField(default='#111925', max_length=20)),
                ('tema', models.CharField(choices=[('escuro', 'Escuro'), ('claro', 'Claro')], default='escuro', max_length=20)),
                ('rodape_pdfs', models.CharField(default='JR Grupo - Gestao de Ativos de TI', max_length=180)),
                ('app_public_url', models.URLField(blank=True, help_text='Quando preenchida, sobrescreve APP_PUBLIC_URL do .env.', verbose_name='URL publica do sistema')),
                ('ultima_sincronizacao', models.DateTimeField(blank=True, null=True)),
                ('ultima_sincronizacao_total', models.PositiveIntegerField(default=0)),
                ('ultimo_backup', models.DateTimeField(blank=True, null=True)),
                ('criado_em', models.DateTimeField(auto_now_add=True)),
                ('atualizado_em', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Configuracao do sistema',
                'verbose_name_plural': 'Configuracoes do sistema',
                'permissions': [('can_manage_configuracoes', 'Pode gerenciar configuracoes')],
            },
        ),
        migrations.CreateModel(
            name='LogSistema',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_hora', models.DateTimeField(auto_now_add=True)),
                ('usuario', models.CharField(blank=True, max_length=150)),
                ('acao', models.CharField(max_length=120)),
                ('resultado', models.TextField(blank=True)),
            ],
            options={
                'verbose_name': 'Log do sistema',
                'verbose_name_plural': 'Logs do sistema',
                'ordering': ['-data_hora'],
            },
        ),
    ]
