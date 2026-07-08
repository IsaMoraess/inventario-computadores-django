"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.urls import path

from ativos.views import (
    api_computadores,
    api_reposicionar_computador,
    configuracoes,
    configuracoes_exportar_banco,
    configuracoes_exportar_configuracoes,
    computador_editar,
    computador_excluir,
    computador_list,
    computador_novo,
    dashboard,
    detalhe_computador,
    gerenciar_plantas,
    mapa,
    qrcode_pdf,
    qrcode_png,
    qrcodes,
    qrcodes_folha_impressao,
    qrcodes_zip,
    relatorio_alertas,
    relatorio_excel,
    relatorio_geral,
    relatorio_movimentacoes,
    relatorio_setor,
    relatorios,
)

urlpatterns = [
    path(
        'login/',
        auth_views.LoginView.as_view(template_name='registration/login.html'),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', dashboard, name='dashboard'),
    path('mapa/', mapa, name='mapa'),
    path('plantas/', gerenciar_plantas, name='gerenciar_plantas'),
    path('qrcodes/', qrcodes, name='qrcodes'),
    path('qrcodes/todos/zip/', qrcodes_zip, name='qrcodes_zip'),
    path('qrcodes/folha-impressao/', qrcodes_folha_impressao, name='qrcodes_folha_impressao'),
    path('qrcodes/<str:id>/png/', qrcode_png, name='qrcode_png'),
    path('qrcodes/<str:id>/pdf/', qrcode_pdf, name='qrcode_pdf'),
    path('relatorios/', relatorios, name='relatorios'),
    path('relatorios/geral/', relatorio_geral, name='relatorio_geral'),
    path('relatorios/setor/', relatorio_setor, name='relatorio_setor'),
    path('relatorios/alertas/', relatorio_alertas, name='relatorio_alertas'),
    path('relatorios/movimentacoes/', relatorio_movimentacoes, name='relatorio_movimentacoes'),
    path('relatorios/excel/', relatorio_excel, name='relatorio_excel'),
    path('configuracoes/', configuracoes, name='configuracoes'),
    path(
        'configuracoes/exportar-banco/',
        configuracoes_exportar_banco,
        name='configuracoes_exportar_banco',
    ),
    path(
        'configuracoes/exportar-configuracoes/',
        configuracoes_exportar_configuracoes,
        name='configuracoes_exportar_configuracoes',
    ),
    path('computadores/', computador_list, name='computador_list'),
    path('computadores/novo/', computador_novo, name='computador_novo'),
    path('computadores/<str:id>/editar/', computador_editar, name='computador_editar'),
    path('computadores/<str:id>/excluir/', computador_excluir, name='computador_excluir'),
    path('computadores/<str:id>/', detalhe_computador, name='detalhe_computador'),
    path('api/computadores/', api_computadores, name='api_computadores'),
    path(
        'api/computadores/<str:id>/reposicionar/',
        api_reposicionar_computador,
        name='api_reposicionar_computador',
    ),
    path('admin/', admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
