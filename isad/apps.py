from django.apps import AppConfig


class IsadConfig(AppConfig):
    name = 'isad'

    def ready(self):
        from . import signals
