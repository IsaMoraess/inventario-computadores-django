from django.db.models.signals import post_save, pre_delete, pre_save
from django.dispatch import receiver

from .middleware import get_current_user
from .models import Computador, Movimentacao, Planta


COMPUTADOR_CAMPOS = (
    'sala',
    'usuario',
    'status',
    'x',
    'y',
    'armazenamento',
    'placa_video',
    'sistema',
    'ram',
    'processador',
    'observacoes',
)

CAMPO_LABELS = {
    'sala': 'Sala',
    'usuario': 'Usuario',
    'status': 'Status',
    'x': 'X',
    'y': 'Y',
    'armazenamento': 'Armazenamento',
    'placa_video': 'Placa de video',
    'sistema': 'Sistema',
    'ram': 'RAM',
    'processador': 'Processador',
    'observacoes': 'Observacoes',
}

CAMPO_ACOES = {
    'sala': 'Sala alterada',
    'usuario': 'Usuario alterado',
    'status': 'Status alterado',
}

CAMPO_TIPOS = {
    'sala': 'sala',
    'usuario': 'usuario',
    'status': 'status',
}


def usuario_responsavel():
    user = get_current_user()

    if not user:
        return 'Sistema'

    nome = user.get_full_name() or user.get_username()
    return nome or 'Sistema'


def valor(valor_original):
    if valor_original is None:
        return ''

    return str(valor_original)


def registrar_movimentacao(
    computador=None,
    computador_identificador='',
    tipo_acao='',
    acao='',
    descricao='',
    campo='',
    valor_anterior='',
    valor_novo='',
):
    if computador is not None and not computador_identificador:
        computador_identificador = computador.pk

    Movimentacao.objects.create(
        computador=computador,
        computador_identificador=computador_identificador,
        tipo_acao=tipo_acao,
        acao=acao,
        descricao=descricao,
        campo=campo,
        valor_anterior=valor(valor_anterior),
        valor_novo=valor(valor_novo),
        usuario_responsavel=usuario_responsavel(),
    )


@receiver(pre_save, sender=Computador)
def guardar_computador_antigo(sender, instance, **kwargs):
    if not instance.pk:
        instance._historico_old_values = None
        return

    antigo = sender.objects.filter(pk=instance.pk).first()
    if not antigo:
        instance._historico_old_values = None
        return

    instance._historico_old_values = {
        campo: getattr(antigo, campo)
        for campo in COMPUTADOR_CAMPOS
    }


@receiver(post_save, sender=Computador)
def registrar_save_computador(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    if created:
        registrar_movimentacao(
            computador=instance,
            tipo_acao='cadastro',
            acao='Computador cadastrado',
            descricao=f'Computador {instance.pk} cadastrado.',
            campo='registro',
            valor_novo=instance.pk,
        )
        return

    antigos = getattr(instance, '_historico_old_values', None)
    if not antigos:
        return

    alterados = {
        campo: (antigos[campo], getattr(instance, campo))
        for campo in COMPUTADOR_CAMPOS
        if valor(antigos[campo]) != valor(getattr(instance, campo))
    }

    if 'x' in alterados or 'y' in alterados:
        x_antigo = antigos.get('x')
        y_antigo = antigos.get('y')
        x_novo = getattr(instance, 'x')
        y_novo = getattr(instance, 'y')
        registrar_movimentacao(
            computador=instance,
            tipo_acao='reposicionamento',
            acao='Reposicionamento',
            descricao='Reposicionado no mapa',
            campo='posicao',
            valor_anterior=f'X: {x_antigo}; Y: {y_antigo}',
            valor_novo=f'X: {x_novo}; Y: {y_novo}',
        )

    for campo, (anterior, novo) in alterados.items():
        if campo in ('x', 'y'):
            continue

        label = CAMPO_LABELS.get(campo, campo)
        acao = CAMPO_ACOES.get(campo, f'{label} alterado')
        registrar_movimentacao(
            computador=instance,
            tipo_acao=CAMPO_TIPOS.get(campo, 'edicao'),
            acao=acao,
            descricao=f'{label} alterado.',
            campo=campo,
            valor_anterior=anterior,
            valor_novo=novo,
        )


@receiver(pre_delete, sender=Computador)
def registrar_delete_computador(sender, instance, **kwargs):
    registrar_movimentacao(
        computador=instance,
        computador_identificador=instance.pk,
        tipo_acao='exclusao',
        acao='Computador excluido',
        descricao=f'Computador {instance.pk} excluido.',
        campo='registro',
        valor_anterior=instance.pk,
        valor_novo='',
    )


@receiver(pre_save, sender=Planta)
def guardar_planta_antiga(sender, instance, **kwargs):
    if not instance.pk:
        instance._historico_old_values = None
        return

    antiga = sender.objects.filter(pk=instance.pk).first()
    if not antiga:
        instance._historico_old_values = None
        return

    instance._historico_old_values = {
        'nome': antiga.nome,
        'imagem': antiga.imagem.name,
        'ativa': antiga.ativa,
    }


@receiver(post_save, sender=Planta)
def registrar_save_planta(sender, instance, created, raw=False, **kwargs):
    if raw:
        return

    if created:
        registrar_movimentacao(
            computador=None,
            computador_identificador='PLANTA',
            tipo_acao='planta',
            acao='Planta cadastrada',
            descricao=f'Planta {instance.nome} cadastrada.',
            campo='planta',
            valor_novo=instance.imagem.name,
        )
        return

    antigos = getattr(instance, '_historico_old_values', None)
    if not antigos:
        return

    if antigos.get('imagem') != instance.imagem.name:
        registrar_movimentacao(
            computador=None,
            computador_identificador='PLANTA',
            tipo_acao='planta',
            acao='Planta alterada',
            descricao=f'Imagem da planta {instance.nome} alterada.',
            campo='imagem',
            valor_anterior=antigos.get('imagem', ''),
            valor_novo=instance.imagem.name,
        )
