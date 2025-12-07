from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """
    Application configuration for the accounts app.

    This app extends the built-in Django User model with a UserProfile,
    and ensures that authentication tokens are created for new users.
    """
    name = 'accounts'

    def ready(self):
        """
        Imports signal handlers when the app is ready.

        The import ensures that the `create_auth_token` signal receiver is
        registered with Django's signal framework.
        """
        super(AccountsConfig, self).ready()
        from accounts.signals import create_auth_token
