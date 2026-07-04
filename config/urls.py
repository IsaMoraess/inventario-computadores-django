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
from django.urls import path

from ativos.views import (
    api_computadores,
    api_reposicionar_computador,
    computador_editar,
    computador_excluir,
    computador_list,
    computador_novo,
    dashboard,
    detalhe_computador,
    mapa,
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('mapa/', mapa, name='mapa'),
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
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
