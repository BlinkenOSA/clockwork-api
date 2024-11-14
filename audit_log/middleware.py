# middleware.py
import threading

_user = threading.local()


class SetUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        skip_paths = [
            '/auth/jwt/create/'
            '/auth/jwt/verify/',
            '/auth/jwt/refresh/',
        ]

        if request.path not in skip_paths:
            _user.value = request.user if request.user.is_authenticated else None
        else:
            _user.value = None
        response = self.get_response(request)
        return response


def get_current_user():
    return getattr(_user, 'value', None)