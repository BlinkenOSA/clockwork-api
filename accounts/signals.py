from typing import Type, Any
from django.contrib.auth.models import User

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_auth_token(
        sender: Type[User],
        instance: User | None = None,
        created: bool = False,
        **kwargs: Any
) -> None:
    """
    Creates an authentication token whenever a new user is created.

    This signal handler listens for post-save events on the AUTH_USER_MODEL
    and automatically generates a DRF Token for token-based authentication.

    Args:
        sender: The model class sending the signal (usually the User model).
        instance: The user instance that was saved.
        created: True if a new user was created, False if an existing user
            was updated.
        **kwargs: Additional keyword arguments from the signal.
    """
    if created:
        Token.objects.create(user=instance)
