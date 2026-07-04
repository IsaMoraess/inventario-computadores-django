from threading import local


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
