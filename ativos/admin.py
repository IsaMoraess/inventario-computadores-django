from django.contrib import admin

from .models import Computador, ConfiguracaoSistema, LogSistema, Movimentacao, Planta
from .services.supabase_sync import atualizar_posicao_supabase


@admin.register(Computador)
class ComputadorAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'sala',
        'status',
        'usuario',
        'sistema',
        'ram',
        'processador',
        'atualizado_em',
    )
    search_fields = (
        'id',
        'sala',
        'usuario',
        'sistema',
        'ram',
        'processador',
        'observacoes',
    )
    list_filter = ('status', 'sala', 'sistema', 'criado_em', 'atualizado_em')
    fields = (
        'id',
        'sala',
        'status',
        'usuario',
        'sistema',
        'ram',
        'processador',
        'armazenamento',
        'placa_video',
        'observacoes',
        'x',
        'y',
    )
    help_texts = {
        'x': 'Posicao horizontal no mapa. Tambem sincronizada com o Supabase ao salvar. Prefira reposicionar pelo Mapa Interativo.',
        'y': 'Posicao vertical no mapa. Tambem sincronizada com o Supabase ao salvar. Prefira reposicionar pelo Mapa Interativo.',
    }

    def get_form(self, request, obj=None, **kwargs):
        kwargs['help_texts'] = self.help_texts
        return super().get_form(request, obj, **kwargs)

    def save_model(self, request, obj, form, change):
        posicao_alterada = change and (
            'x' in form.changed_data or 'y' in form.changed_data
        )
        super().save_model(request, obj, form, change)

        if posicao_alterada:
            atualizar_posicao_supabase(obj.id, obj.x, obj.y)


@admin.register(Movimentacao)
class MovimentacaoAdmin(admin.ModelAdmin):
    list_display = (
        'computador',
        'computador_identificador',
        'tipo_acao',
        'acao',
        'campo',
        'descricao',
        'usuario_responsavel',
        'data_hora',
    )
    readonly_fields = (
        'computador',
        'computador_identificador',
        'tipo_acao',
        'descricao',
        'usuario_responsavel',
        'valor_anterior',
        'valor_novo',
        'acao',
        'data_hora',
    )
    search_fields = (
        'computador__id',
        'computador_identificador',
        'tipo_acao',
        'descricao',
        'usuario_responsavel',
        'campo',
        'valor_anterior',
        'valor_novo',
        'acao',
    )
    list_filter = ('tipo_acao', 'campo', 'acao', 'usuario_responsavel', 'data_hora')


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa', 'criada_em')
    search_fields = ('nome',)
    list_filter = ('ativa', 'criada_em')


@admin.register(ConfiguracaoSistema)
class ConfiguracaoSistemaAdmin(admin.ModelAdmin):
    list_display = (
        'nome_empresa',
        'tema',
        'app_public_url',
        'ultima_sincronizacao',
        'ultimo_backup',
        'atualizado_em',
    )

    def has_add_permission(self, request):
        return not ConfiguracaoSistema.objects.exists()


@admin.register(LogSistema)
class LogSistemaAdmin(admin.ModelAdmin):
    list_display = ('data_hora', 'usuario', 'acao', 'resultado')
    search_fields = ('usuario', 'acao', 'resultado')
    list_filter = ('acao', 'data_hora')
    readonly_fields = ('data_hora', 'usuario', 'acao', 'resultado')
