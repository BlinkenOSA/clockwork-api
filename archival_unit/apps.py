from django.apps import AppConfig


class ArchivalUnitConfig(AppConfig):
    """
    Application configuration for the `archival_unit` app.

    This app manages hierarchical archival units (fonds, subfonds, series)
    and their descriptive metadata. When the app is ready, it ensures that all
    associated signal handlers are imported so that they register correctly with
    Django's signal dispatching system.
    """
    name = 'archival_unit'

    def ready(self):
        """
        Imports signal handlers when the application is initialized.

        The import is executed for its side effects (registering signal
        receivers). It must remain inside this method to avoid premature
        module-level imports while Django is still configuring apps.
        """
        from . import signals