from django.apps import AppConfig


class FindingAidsConfig(AppConfig):
    """
    Application configuration for the finding_aids module.

    This app manages finding aids entities and their associated behaviors,
    including publication state changes and indexing side effects.
    """

    name = 'finding_aids'

    def ready(self):
        """
        Imports signal handlers when the application is ready.

        Signal registration is deferred to ensure models are fully loaded
        before signals are connected.
        """
        from . import signals
