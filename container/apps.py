from django.apps import AppConfig


class ContainerConfig(AppConfig):
    """
    Application configuration for the container domain.

    This app is responsible for managing physical and logical containers,
    including their identifiers, relationships, and lifecycle events
    within the system.
    """
    name = 'container'

    def ready(self):
        """
        Registers container-related signal handlers.

        Importing the signals module ensures that all model signal
        receivers are connected when the application is initialized.
        """
        from . import signals