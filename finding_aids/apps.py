from django.apps import AppConfig


class FindingAidsConfig(AppConfig):
    name = 'finding_aids'

    def ready(self):
        from . import signals
