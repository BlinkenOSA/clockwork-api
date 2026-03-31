from django.conf import settings
import requests


DEFAULT_TIMEOUT = getattr(settings, "REQUESTS_TIMEOUT", 5)


def _apply_timeout(kwargs):
    if "timeout" not in kwargs or kwargs["timeout"] is None:
        kwargs["timeout"] = DEFAULT_TIMEOUT
    return kwargs


def request(method, url, **kwargs):
    return requests.request(method, url, **_apply_timeout(kwargs))


def get(url, **kwargs):
    return request("GET", url, **kwargs)


def post(url, **kwargs):
    return request("POST", url, **kwargs)


class Session(requests.Session):
    def request(self, method, url, **kwargs):
        return super().request(method, url, **_apply_timeout(kwargs))
