from django.apps import AppConfig


class ContainerConfig(AppConfig):
    name = 'container'

    def ready(self):
        from . import signals