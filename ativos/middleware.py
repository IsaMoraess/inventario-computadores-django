from threading import local

from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect

from .permissions import is_admin_profile


_state = local()


class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _state.user = getattr(request, 'user', None)
        try:
            return self.get_response(request)
        finally:
            _state.user = None


def get_current_user():
    user = getattr(_state, 'user', None)

    if user is not None and getattr(user, 'is_authenticated', False):
        return user

    return None


class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/'):
            user = getattr(request, 'user', None)

            if not user or not user.is_authenticated:
                return redirect('login')

            if not is_admin_profile(user):
                raise PermissionDenied

        return self.get_response(request)
