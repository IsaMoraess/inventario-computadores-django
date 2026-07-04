import unicodedata
import json
from base64 import b64encode
from collections import Counter
from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

import qrcode

from .forms import ComputadorForm
from .models import Computador, Movimentacao, Planta


PENDENCIA_TERMOS = (
    'nao informado',
    'não informado',
    'ninguem',
    'ninguém',
    'sem usuario',
    'sem usuário',
)

PENDENCIA_CAMPOS = (
    'usuario',
    'sistema',
    'ram',
    'processador',
    'armazenamento',
)


def _normalizar(valor):
    valor = (valor or '').strip().lower()
    return ''.join(
        char
        for char in unicodedata.normalize('NFKD', valor)
        if not unicodedata.combining(char)
    )


def _rotulo(valor, fallback='Não informado'):
    valor = (valor or '').strip()
    return valor if valor else fallback


def _pendencias_q():
    query = Q()

    for campo in PENDENCIA_CAMPOS:
        query |= Q(**{f'{campo}__isnull': True})
        query |= Q(**{campo: ''})
        for termo in PENDENCIA_TERMOS:
            query |= Q(**{f'{campo}__iexact': termo})
            query |= Q(**{f'{campo}__icontains': termo})

    return query


def _motivos_pendencia(computador):
    motivos = []

    for campo in PENDENCIA_CAMPOS:
        valor = getattr(computador, campo, '')
        normalizado = _normalizar(valor)
        nome_campo = campo.replace('_', ' ').title()

        if not normalizado:
            motivos.append(f'{nome_campo} vazio')
        elif any(_normalizar(termo) in normalizado for termo in PENDENCIA_TERMOS):
            motivos.append(f'{nome_campo}: {_rotulo(valor)}')

    return motivos


def _contar_status(computadores):
    contagem = Counter()

    for status in computadores.values_list('status', flat=True):
        normalizado = _normalizar(status)

        if normalizado.startswith('ativo'):
            contagem['ativos'] += 1
        elif 'manuten' in normalizado:
            contagem['manutencao'] += 1
        elif 'desligado' in normalizado:
            contagem['desligados'] += 1
        elif 'reserva' in normalizado:
            contagem['reservas'] += 1

    return contagem


def _status_css_class(status):
    normalizado = _normalizar(status)

    if 'manuten' in normalizado:
        return 'status-manutencao'
    if 'reserva' in normalizado:
        return 'status-reserva'
    if 'desligado' in normalizado:
        return 'status-desligado'
    return 'status-ativo'


def _contar_windows(computadores):
    contagem = Counter({'Windows 10': 0, 'Windows 11': 0, 'Outros / Não informado': 0})

    for sistema in computadores.values_list('sistema', flat=True):
        normalizado = _normalizar(sistema)

        if 'windows 11' in normalizado or normalizado == 'win11':
            contagem['Windows 11'] += 1
        elif 'windows 10' in normalizado or normalizado == 'win10':
            contagem['Windows 10'] += 1
        else:
            contagem['Outros / Não informado'] += 1

    return contagem


def _grafico_por_campo(computadores, campo, fallback='Nao informado', limite=None, ordenar_por_total=True):
    ordenacao = ['-total', campo] if ordenar_por_total else [campo]
    grupos = computadores.values(campo).annotate(total=Count('id')).order_by(*ordenacao)

    if limite:
        grupos = grupos[:limite]

    dados = []
    for item in grupos:
        valor = item[campo]
        ids = list(
            computadores.filter(**{campo: valor})
            .order_by('id')
            .values_list('id', flat=True)
        )
        dados.append(
            {
                'label': _rotulo(valor, fallback),
                'value': item['total'],
                'ids': ids,
            }
        )

    return dados


def _grafico_windows(computadores):
    grupos = {
        'Windows 10': [],
        'Windows 11': [],
        'Outros / Nao informado': [],
    }

    for computador in computadores.only('id', 'sistema').order_by('id'):
        normalizado = _normalizar(computador.sistema)

        if 'windows 11' in normalizado or normalizado == 'win11':
            grupos['Windows 11'].append(computador.id)
        elif 'windows 10' in normalizado or normalizado == 'win10':
            grupos['Windows 10'].append(computador.id)
        else:
            grupos['Outros / Nao informado'].append(computador.id)

    return [
        {
            'label': label,
            'value': len(ids),
            'ids': ids,
        }
        for label, ids in grupos.items()
    ]


def dashboard(request):
    computadores = Computador.objects.all()
    pendencias_query = _pendencias_q()
    pendencias_qs = computadores.filter(pendencias_query).distinct()
    alertas_qs = computadores.filter(
        pendencias_query | Q(status__icontains='manuten') | ~Q(observacoes='')
    ).distinct()

    status_cards = _contar_status(computadores)
    status_grafico = _grafico_por_campo(computadores, 'status', ordenar_por_total=False)
    salas_grafico = _grafico_por_campo(computadores, 'sala', fallback='Sem sala', limite=8)
    ram_grafico = _grafico_por_campo(computadores, 'ram', limite=8)
    windows_grafico = _grafico_windows(computadores)
    pendencias = [
        {
            'computador': computador,
            'motivos': _motivos_pendencia(computador),
        }
        for computador in pendencias_qs.order_by('sala', 'id')[:10]
    ]

    context = {
        'page_title': 'Dashboard',
        'cards': {
            'total': computadores.count(),
            'ativos': status_cards['ativos'],
            'manutencao': status_cards['manutencao'],
            'desligados': status_cards['desligados'],
            'reservas': status_cards['reservas'],
            'setores_salas': computadores.exclude(sala='').values('sala').distinct().count(),
            'alertas': alertas_qs.count(),
        },
        'ultimas_movimentacoes': Movimentacao.objects.select_related('computador')[:8],
        'pendencias': pendencias,
        'total_pendencias': pendencias_qs.count(),
        'chart_data': {
            'status': status_grafico,
            'salas': salas_grafico,
            'windows': windows_grafico,
            'ram': ram_grafico,
        },
    }

    return render(request, 'ativos/dashboard.html', context)


def computador_list(request):
    computadores = Computador.objects.all()
    busca = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    sala = (request.GET.get('sala') or '').strip()
    sistema = (request.GET.get('sistema') or '').strip()

    if busca:
        computadores = computadores.filter(
            Q(id__icontains=busca)
            | Q(usuario__icontains=busca)
            | Q(sala__icontains=busca)
            | Q(sistema__icontains=busca)
            | Q(ram__icontains=busca)
            | Q(processador__icontains=busca)
        )

    if status:
        computadores = computadores.filter(status=status)
    if sala:
        computadores = computadores.filter(sala=sala)
    if sistema:
        computadores = computadores.filter(sistema=sistema)

    context = {
        'page_title': 'Computadores',
        'computadores': computadores.order_by('sala', 'id'),
        'busca': busca,
        'status_filtro': status,
        'sala_filtro': sala,
        'sistema_filtro': sistema,
        'status_options': Computador.Status.choices,
        'salas': Computador.objects.exclude(sala='').values_list('sala', flat=True).distinct().order_by('sala'),
        'sistemas': Computador.objects.exclude(sistema='').values_list('sistema', flat=True).distinct().order_by('sistema'),
    }

    return render(request, 'ativos/computador_list.html', context)


def computador_novo(request):
    form = ComputadorForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        computador = form.save()
        messages.success(request, f'Computador {computador.id} cadastrado com sucesso.')
        return redirect('detalhe_computador', id=computador.id)

    return render(
        request,
        'ativos/computador_form.html',
        {
            'page_title': 'Novo computador',
            'form': form,
            'form_title': 'Novo computador',
            'submit_label': 'Cadastrar computador',
        },
    )


def computador_editar(request, id):
    computador = get_object_or_404(Computador, pk=id)
    form = ComputadorForm(request.POST or None, instance=computador)

    if request.method == 'POST' and form.is_valid():
        computador = form.save()
        messages.success(request, f'Computador {computador.id} atualizado com sucesso.')
        return redirect('detalhe_computador', id=computador.id)

    return render(
        request,
        'ativos/computador_form.html',
        {
            'page_title': f'Editar {computador.id}',
            'form': form,
            'computador': computador,
            'form_title': f'Editar {computador.id}',
            'submit_label': 'Salvar alteracoes',
        },
    )


def computador_excluir(request, id):
    computador = get_object_or_404(Computador, pk=id)

    if request.method == 'POST':
        computador_id = computador.id
        computador.delete()
        messages.success(request, f'Computador {computador_id} excluido com sucesso.')
        return redirect('computador_list')

    return render(
        request,
        'ativos/computador_confirm_delete.html',
        {
            'page_title': f'Excluir {computador.id}',
            'computador': computador,
        },
    )


@ensure_csrf_cookie
def mapa(request):
    planta = Planta.objects.filter(ativa=True).first() or Planta.objects.first()

    return render(
        request,
        'ativos/mapa.html',
        {
            'page_title': 'Mapa Interativo',
            'planta': planta,
        },
    )


def _qr_code_data_url(valor):
    buffer = BytesIO()
    imagem = qrcode.make(valor)
    imagem.save(buffer, format='PNG')
    codigo = b64encode(buffer.getvalue()).decode('ascii')

    return f'data:image/png;base64,{codigo}'


def _public_url(path, request=None):
    if settings.APP_PUBLIC_URL:
        return f'{settings.APP_PUBLIC_URL}{path}'

    if request is not None:
        return request.build_absolute_uri(path)

    return path


def _computador_public_url(computador, request=None):
    return _public_url(reverse('detalhe_computador', args=[computador.pk]), request)


def detalhe_computador(request, id):
    computador = get_object_or_404(Computador, pk=id)
    admin_edit_url = reverse('admin:ativos_computador_change', args=[computador.pk])
    edit_url = reverse('computador_editar', args=[computador.pk])
    public_url = _computador_public_url(computador, request)
    movimentacoes = Movimentacao.objects.filter(
        Q(computador=computador) | Q(computador_identificador=computador.pk)
    ).distinct()

    return render(
        request,
        'ativos/detalhe_computador.html',
        {
            'page_title': f'Computador {computador.id}',
            'computador': computador,
            'movimentacoes': movimentacoes,
            'admin_edit_url': admin_edit_url,
            'edit_url': edit_url,
            'public_url': public_url,
            'qr_code': _qr_code_data_url(public_url),
            'status_class': _status_css_class(computador.status),
        },
    )


def api_computadores(request):
    computadores = Computador.objects.order_by('sala', 'id')
    dados = []

    for computador in computadores:
        detalhe_url = reverse('detalhe_computador', args=[computador.pk])
        editar_url = reverse('computador_editar', args=[computador.pk])
        admin_edit_url = reverse('admin:ativos_computador_change', args=[computador.pk])
        qr_url = _computador_public_url(computador, request)
        dados.append(
            {
                'id': computador.id,
                'nome': computador.id,
                'usuario': computador.usuario,
                'sala': computador.sala,
                'status': computador.status,
                'ram': computador.ram,
                'sistema': computador.sistema,
                'processador': computador.processador,
                'armazenamento': computador.armazenamento,
                'placa_video': computador.placa_video,
                'x': computador.x,
                'y': computador.y,
                'qr_code': _qr_code_data_url(qr_url),
                'detail_url': detalhe_url,
                'edit_url': editar_url,
                'admin_edit_url': admin_edit_url,
            }
        )

    return JsonResponse({'computadores': dados})


@require_POST
def api_reposicionar_computador(request, id):
    computador = get_object_or_404(Computador, pk=id)

    try:
        dados = json.loads(request.body.decode('utf-8') or '{}')
        x = int(dados.get('x'))
        y = int(dados.get('y'))
    except (TypeError, ValueError, json.JSONDecodeError):
        return JsonResponse(
            {'ok': False, 'error': 'Coordenadas invalidas.'},
            status=400,
        )

    if x < 0 or y < 0:
        return JsonResponse(
            {'ok': False, 'error': 'As coordenadas nao podem ser negativas.'},
            status=400,
        )

    computador.x = x
    computador.y = y
    computador.save(update_fields=['x', 'y', 'atualizado_em'])

    return JsonResponse(
        {
            'ok': True,
            'computador': {
                'id': computador.id,
                'x': computador.x,
                'y': computador.y,
            },
        }
    )
