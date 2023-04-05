from django.apps import AppConfig


class ArchivalUnitConfig(AppConfig):
    name = 'archival_unit'

    def ready(self):
        from . import signals