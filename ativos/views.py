import json

from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from django.db import transaction
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_date
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .forms import ComputadorForm, ConfiguracaoSistemaForm, PlantaForm
from .models import Computador, LogSistema, Movimentacao, Planta
from .permissions import (
    PERM_ADD_COMPUTER,
    PERM_CHANGE_COMPUTER,
    PERM_DELETE_COMPUTER,
    PERM_DOWNLOAD_QRCODES,
    PERM_DOWNLOAD_REPORTS,
    PERM_MANAGE_CONFIGURACOES,
    PERM_MANAGE_PLANTS,
    PERM_REPOSITION,
    PERM_VIEW_COMPUTER,
    login_and_permission,
)
from .services import configuracao_service, excel_service, qrcode_service, relatorio_service
from .services.supabase_sync import atualizar_posicao_supabase
from .services.inventario_metrics import (
    computadores_com_alerta,
    contar_status,
    grafico_por_campo,
    grafico_windows,
    motivos_pendencia,
    pendencias_q,
    status_css_class,
)


@login_and_permission(PERM_VIEW_COMPUTER)
def dashboard(request):
    computadores = Computador.objects.all()
    pendencias_query = pendencias_q()
    pendencias_qs = computadores.filter(pendencias_query).distinct()
    alertas = computadores_com_alerta(computadores)

    status_cards = contar_status(computadores)
    status_grafico = grafico_por_campo(computadores, 'status', ordenar_por_total=False)
    salas_grafico = grafico_por_campo(computadores, 'sala', fallback='Sem sala', limite=8)
    ram_grafico = grafico_por_campo(computadores, 'ram', limite=8)
    windows_grafico = grafico_windows(computadores)
    pendencias = [
        {
            'computador': computador,
            'motivos': motivos_pendencia(computador),
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
            'alertas': len(alertas),
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


@login_and_permission(PERM_VIEW_COMPUTER)
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


@login_and_permission(PERM_ADD_COMPUTER)
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


@login_and_permission(PERM_CHANGE_COMPUTER)
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


@login_and_permission(PERM_DELETE_COMPUTER)
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


def _definir_planta_ativa(planta):
    for outra_planta in Planta.objects.filter(ativa=True).exclude(pk=planta.pk):
        outra_planta.ativa = False
        outra_planta.save(update_fields=['ativa'])

    if not planta.ativa:
        planta.ativa = True
        planta.save(update_fields=['ativa'])


@login_and_permission(PERM_MANAGE_PLANTS)
def gerenciar_plantas(request):
    form = PlantaForm()

    if request.method == 'POST':
        acao = request.POST.get('action') or 'upload'

        if acao == 'ativar':
            planta = get_object_or_404(Planta, pk=request.POST.get('planta_id'))

            with transaction.atomic():
                _definir_planta_ativa(planta)

            messages.success(request, f'Planta "{planta.nome}" definida como ativa.')
            return redirect('gerenciar_plantas')

        form = PlantaForm(request.POST, request.FILES)
        if form.is_valid():
            definir_ativa = form.cleaned_data['definir_ativa']

            with transaction.atomic():
                planta = form.save(commit=False)
                planta.ativa = definir_ativa or not Planta.objects.filter(ativa=True).exists()

                if planta.ativa:
                    for outra_planta in Planta.objects.filter(ativa=True):
                        outra_planta.ativa = False
                        outra_planta.save(update_fields=['ativa'])

                planta.save()

            messages.success(request, f'Planta "{planta.nome}" cadastrada com sucesso.')
            return redirect('gerenciar_plantas')

    return render(
        request,
        'ativos/plantas.html',
        {
            'page_title': 'Plantas',
            'form': form,
            'plantas': Planta.objects.all(),
        },
    )


def _qrcode_queryset(request):
    computadores = Computador.objects.all()
    busca = (request.GET.get('q') or '').strip()
    status = (request.GET.get('status') or '').strip()
    sala = (request.GET.get('sala') or '').strip()

    if busca:
        computadores = computadores.filter(
            Q(id__icontains=busca)
            | Q(usuario__icontains=busca)
            | Q(sala__icontains=busca)
            | Q(status__icontains=busca)
        )

    if status:
        computadores = computadores.filter(status=status)
    if sala:
        computadores = computadores.filter(sala=sala)

    return computadores.order_by('sala', 'id'), busca, status, sala


def _qr_size(request, default=900):
    try:
        size = int(request.GET.get('size', default))
    except (TypeError, ValueError):
        size = default

    return min(max(size, 320), 1800)


def _download_response(content, content_type, filename, inline=False):
    response = HttpResponse(content, content_type=content_type)
    disposition = 'inline' if inline else 'attachment'
    response['Content-Disposition'] = f'{disposition}; filename="{filename}"'
    return response


def _usuarios_online_count():
    sessions = Session.objects.filter(expire_date__gte=timezone.now())
    user_ids = set()

    for session in sessions:
        data = session.get_decoded()
        user_id = data.get('_auth_user_id')
        if user_id:
            user_ids.add(user_id)

    return len(user_ids)


@login_and_permission(PERM_MANAGE_CONFIGURACOES)
def configuracoes(request):
    config = configuracao_service.get_config()
    form = ConfiguracaoSistemaForm(instance=config)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'salvar_configuracoes':
            form = ConfiguracaoSistemaForm(request.POST, request.FILES, instance=config)
            if form.is_valid():
                form.save()
                configuracao_service.registrar_log(
                    request.user,
                    'Configuracoes atualizadas',
                    'Dados da empresa e interface atualizados.',
                )
                messages.success(request, 'Configuracoes salvas com sucesso.')
                return redirect('configuracoes')

        elif action == 'sincronizar_supabase':
            try:
                resultado = configuracao_service.sincronizar_supabase(request.user)
                messages.success(
                    request,
                    (
                        'Sincronizacao concluida. '
                        f"Criados: {resultado['criados']}; "
                        f"Atualizados: {resultado['atualizados']}; "
                        f"Removidos: {resultado['removidos']}; "
                        f"Ignorados: {resultado['ignorados']}; "
                        f"Erros: {resultado['erros']}."
                    ),
                )
                for aviso in resultado.get('avisos', [])[:5]:
                    messages.warning(request, aviso)
            except Exception as error:
                configuracao_service.registrar_log(
                    request.user,
                    'Sincronizacao Supabase',
                    f'Erro: {type(error).__name__}: {error}',
                )
                messages.error(request, f'Erro ao sincronizar Supabase: {error}')
            return redirect('configuracoes')

        elif action == 'importar_banco':
            arquivo = request.FILES.get('arquivo_json')
            if not arquivo:
                messages.error(request, 'Selecione um arquivo JSON para importar.')
            else:
                try:
                    total = configuracao_service.importar_banco_json(arquivo, request.user)
                    messages.success(request, f'Importacao concluida: {total} registros processados.')
                except Exception as error:
                    configuracao_service.registrar_log(
                        request.user,
                        'Backup importado',
                        f'Erro: {type(error).__name__}: {error}',
                    )
                    messages.error(request, f'Erro ao importar backup: {error}')
            return redirect('configuracoes')

        elif action == 'limpar_cache':
            configuracao_service.limpar_cache(request.user)
            messages.success(request, 'Cache limpo com sucesso.')
            return redirect('configuracoes')

        elif action == 'recarregar_estatisticas':
            configuracao_service.registrar_log(
                request.user,
                'Estatisticas recarregadas',
                'Dashboard de configuracoes recalculado.',
            )
            messages.success(request, 'Estatisticas recarregadas.')
            return redirect('configuracoes')

        elif action == 'validar_sistema':
            try:
                resultado = configuracao_service.system_check(request.user)
                messages.success(request, resultado)
            except Exception as error:
                configuracao_service.registrar_log(
                    request.user,
                    'Validacao do sistema',
                    f'Erro: {type(error).__name__}: {error}',
                )
                messages.error(request, f'Erro na validacao: {error}')
            return redirect('configuracoes')

    ultimo_login = User.objects.exclude(last_login__isnull=True).order_by('-last_login').first()
    logs = LogSistema.objects.all()[:20]

    context = {
        'page_title': 'Configuracoes',
        'form': form,
        'configuracao': config,
        'logs': logs,
        'sistema': {
            'versao': '2.0',
            'computadores': Computador.objects.count(),
            'plantas': Planta.objects.count(),
            'movimentacoes': Movimentacao.objects.count(),
            'banco_conectado': configuracao_service.banco_conectado(),
            'ultimo_backup': config.ultimo_backup,
            'tempo_online': configuracao_service.tempo_online(),
        },
        'seguranca': {
            'usuarios_online': _usuarios_online_count(),
            'ultimo_login': ultimo_login,
            'tentativas_login': LogSistema.objects.filter(acao__icontains='login').count(),
        },
    }
    return render(request, 'ativos/configuracoes.html', context)


@login_and_permission(PERM_MANAGE_CONFIGURACOES)
def configuracoes_exportar_banco(request):
    content = configuracao_service.exportar_banco_json(request.user)
    return _download_response(content, 'application/json', 'backup_inventario_ativos_ti.json')


@login_and_permission(PERM_MANAGE_CONFIGURACOES)
def configuracoes_exportar_configuracoes(request):
    content = configuracao_service.exportar_configuracoes_json(request.user)
    return _download_response(content, 'application/json', 'configuracoes_sistema.json')


@login_and_permission(PERM_VIEW_COMPUTER)
def qrcodes(request):
    computadores, busca, status, sala = _qrcode_queryset(request)
    computadores = list(computadores)
    qr_size = _qr_size(request)
    itens = [
        {
            'computador': computador,
            'qr_code': qrcode_service.computador_qr_data_url(computador, request, size=360),
        }
        for computador in computadores
    ]

    return render(
        request,
        'ativos/qrcodes.html',
        {
            'page_title': 'QR Codes',
            'itens': itens,
            'total': len(itens),
            'busca': busca,
            'status_filtro': status,
            'sala_filtro': sala,
            'qr_size': qr_size,
            'status_options': Computador.Status.choices,
            'salas': Computador.objects.exclude(sala='').values_list('sala', flat=True).distinct().order_by('sala'),
        },
    )


@login_and_permission(PERM_VIEW_COMPUTER)
def qrcode_png(request, id):
    if request.GET.get('inline') != '1' and not request.user.has_perm(PERM_DOWNLOAD_QRCODES):
        from django.core.exceptions import PermissionDenied

        raise PermissionDenied

    computador = get_object_or_404(Computador, pk=id)
    content = qrcode_service.computador_qr_png_bytes(
        computador,
        request,
        size=_qr_size(request),
    )
    filename = f'{qrcode_service.safe_filename(computador.id)}.png'
    return _download_response(
        content,
        'image/png',
        filename,
        inline=request.GET.get('inline') == '1',
    )


@login_and_permission(PERM_DOWNLOAD_QRCODES)
def qrcode_pdf(request, id):
    computador = get_object_or_404(Computador, pk=id)
    content = qrcode_service.computador_qr_pdf_bytes(computador, request)
    filename = f'{qrcode_service.safe_filename(computador.id)}.pdf'
    return _download_response(content, 'application/pdf', filename)


@login_and_permission(PERM_DOWNLOAD_QRCODES)
def qrcodes_zip(request):
    computadores = Computador.objects.order_by('sala', 'id')
    content = qrcode_service.qrcodes_zip_bytes(
        computadores,
        request,
        size=_qr_size(request),
    )
    return _download_response(content, 'application/zip', 'qrcodes-computadores.zip')


@login_and_permission(PERM_DOWNLOAD_QRCODES)
def qrcodes_folha_impressao(request):
    computadores = Computador.objects.order_by('sala', 'id')
    content = qrcode_service.folha_impressao_pdf_bytes(computadores, request)
    return _download_response(content, 'application/pdf', 'folha-qrcodes-jr-grupo.pdf')


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorios(request):
    return render(
        request,
        'ativos/relatorios.html',
        {
            'page_title': 'Relatorios',
            'salas': Computador.objects.exclude(sala='').values_list('sala', flat=True).distinct().order_by('sala'),
            'computadores': Computador.objects.order_by('id').values_list('id', flat=True),
        },
    )


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorio_geral(request):
    computadores = Computador.objects.all()
    movimentacoes = Movimentacao.objects.select_related('computador').order_by('-data_hora')
    content = relatorio_service.relatorio_geral_pdf(computadores, movimentacoes)
    return _download_response(content, 'application/pdf', 'relatorio_geral_inventario.pdf')


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorio_setor(request):
    sala = (request.GET.get('sala') or '').strip()
    if not sala:
        messages.error(request, 'Selecione uma sala para gerar o relatorio.')
        return redirect('relatorios')

    computadores = Computador.objects.filter(sala=sala)
    content = relatorio_service.relatorio_setor_pdf(computadores, sala)
    filename = f'relatorio_setor_{qrcode_service.safe_filename(sala)}.pdf'
    return _download_response(content, 'application/pdf', filename)


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorio_alertas(request):
    computadores = Computador.objects.all()
    content = relatorio_service.relatorio_alertas_pdf(computadores)
    return _download_response(content, 'application/pdf', 'relatorio_alertas.pdf')


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorio_movimentacoes(request):
    movimentacoes = Movimentacao.objects.select_related('computador').order_by('-data_hora')
    computador_id = (request.GET.get('computador') or '').strip()
    data_inicio_raw = (request.GET.get('data_inicio') or '').strip()
    data_fim_raw = (request.GET.get('data_fim') or '').strip()
    data_inicio = parse_date(data_inicio_raw) if data_inicio_raw else None
    data_fim = parse_date(data_fim_raw) if data_fim_raw else None

    if computador_id:
        movimentacoes = movimentacoes.filter(
            Q(computador_id=computador_id) | Q(computador_identificador=computador_id)
        )
    if data_inicio:
        movimentacoes = movimentacoes.filter(data_hora__date__gte=data_inicio)
    if data_fim:
        movimentacoes = movimentacoes.filter(data_hora__date__lte=data_fim)

    content = relatorio_service.relatorio_movimentacoes_pdf(
        movimentacoes,
        {
            'computador': computador_id,
            'data_inicio': data_inicio_raw,
            'data_fim': data_fim_raw,
        },
    )
    return _download_response(content, 'application/pdf', 'relatorio_movimentacoes.pdf')


@login_and_permission(PERM_DOWNLOAD_REPORTS)
def relatorio_excel(request):
    computadores = Computador.objects.all()
    movimentacoes = Movimentacao.objects.select_related('computador').order_by('-data_hora')
    content = excel_service.inventario_completo_xlsx(computadores, movimentacoes)
    return _download_response(
        content,
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'inventario_ativos_ti_completo.xlsx',
    )


@ensure_csrf_cookie
@login_and_permission(PERM_VIEW_COMPUTER)
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


@login_and_permission(PERM_VIEW_COMPUTER)
def detalhe_computador(request, id):
    computador = get_object_or_404(Computador, pk=id)
    admin_edit_url = reverse('admin:ativos_computador_change', args=[computador.pk])
    edit_url = reverse('computador_editar', args=[computador.pk])
    public_url = qrcode_service.computador_public_url(computador, request)
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
            'qr_code': qrcode_service.computador_qr_data_url(computador, request, size=620),
            'status_class': status_css_class(computador.status),
        },
    )


@login_and_permission(PERM_VIEW_COMPUTER)
def api_computadores(request):
    computadores = Computador.objects.order_by('sala', 'id')
    dados = []

    for computador in computadores:
        detalhe_url = reverse('detalhe_computador', args=[computador.pk])
        editar_url = reverse('computador_editar', args=[computador.pk])
        admin_edit_url = reverse('admin:ativos_computador_change', args=[computador.pk])
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
                'qr_code_url': f'{reverse("qrcode_png", args=[computador.pk])}?inline=1&size=420',
                'detail_url': detalhe_url,
                'edit_url': editar_url,
                'admin_edit_url': admin_edit_url,
            }
        )

    return JsonResponse({'computadores': dados})


@require_POST
@login_and_permission(PERM_REPOSITION)
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

    supabase_sincronizado = atualizar_posicao_supabase(computador.id, x, y)

    return JsonResponse(
        {
            'ok': True,
            'supabase_sincronizado': supabase_sincronizado,
            'computador': {
                'id': computador.id,
                'x': computador.x,
                'y': computador.y,
            },
        }
    )
