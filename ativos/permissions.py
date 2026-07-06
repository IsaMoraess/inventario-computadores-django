from functools import wraps

from django.contrib.auth.decorators import login_required, permission_required


ADMIN_GROUP = 'Administrador'
TI_GROUP = 'TI'
READ_GROUP = 'Leitura'

PERM_ADD_COMPUTER = 'ativos.add_computador'
PERM_VIEW_COMPUTER = 'ativos.view_computador'
PERM_CHANGE_COMPUTER = 'ativos.change_computador'
PERM_DELETE_COMPUTER = 'ativos.delete_computador'
PERM_REPOSITION = 'ativos.can_reposition_computador'
PERM_DOWNLOAD_QRCODES = 'ativos.can_download_qrcodes'
PERM_DOWNLOAD_REPORTS = 'ativos.can_download_reports'
PERM_MANAGE_PLANTS = 'ativos.can_manage_plantas'
PERM_MANAGE_CONFIGURACOES = 'ativos.can_manage_configuracoes'


def in_group(user, group_name):
    return bool(
        user
        and user.is_authenticated
        and (user.is_superuser or user.groups.filter(name=group_name).exists())
    )


def is_admin_profile(user):
    return in_group(user, ADMIN_GROUP)


def login_and_permission(permission):
    def decorator(view_func):
        return login_required(permission_required(permission, raise_exception=True)(view_func))

    return decorator


def login_required_view(view_func):
    return login_required(view_func)
