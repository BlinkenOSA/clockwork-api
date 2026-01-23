from django.apps import AppConfig


class IsadConfig(AppConfig):
    """
    Application configuration for the ISAD app.

    The ISAD app provides support for ISAD(G) descriptive records and related
    archival description functionality.

    The ``ready`` hook imports the app's signal handlers to ensure they are
    registered when the application is loaded.
    """

    name = 'isad'

    def ready(self):
        """
        Imports signal handlers for the ISAD app.

        This method is called when the Django application registry is fully
        populated. Importing the ``signals`` module here ensures that all
        signal receivers are registered at startup.
        """
        from . import signals
