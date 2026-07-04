from django.contrib import admin

from .models import Computador, Movimentacao, Planta


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
