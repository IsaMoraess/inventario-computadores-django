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
        'campo',
        'valor_anterior',
        'valor_novo',
        'acao',
        'data_hora',
    )
    search_fields = (
        'computador__id',
        'campo',
        'valor_anterior',
        'valor_novo',
        'acao',
    )
    list_filter = ('campo', 'acao', 'data_hora')


@admin.register(Planta)
class PlantaAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativa', 'criada_em')
    search_fields = ('nome',)
    list_filter = ('ativa', 'criada_em')
