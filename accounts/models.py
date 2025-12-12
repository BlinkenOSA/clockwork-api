from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE

from archival_unit.models import ArchivalUnit


class UserProfile(models.Model):
    """
    Extends the built-in Django User model with access restrictions.

    Each user may be associated with a set of allowed archival units.
    These units typically represent the scope within which the user is
    permitted to perform certain operations, depending on the application's
    authorization model.

    Attributes:
      user (User):
          One-to-one relation to Django's authentication user model.
          Exposed via the reverse related name ``user_profile``.

      allowed_archival_units (ManyToMany[ArchivalUnit]):
          A collection of archival units that the user is explicitly allowed
          to access. The available choices are restricted to units whose
          level is ``"S"`` (Series level).

    Methods:
      assigned_archival_units():
          Returns the number of archival units assigned to this user.

      __str__():
          Returns the username for display in the Django admin interface.
    """
    user = models.OneToOneField(User, unique=True, verbose_name='user', related_name='user_profile', on_delete=CASCADE)
    allowed_archival_units = models.ManyToManyField(ArchivalUnit, limit_choices_to={'level': 'S'}, blank=True)

    def assigned_archival_units(self) -> int:
        """
        Returns the number of archival units assigned to the user.

        Returns:
            int: Count of allowed archival units.
        """
        return self.allowed_archival_units.count()

    def __str__(self) -> str:
        """Returns the username associated with this profile."""
        return self.user.username

    class Meta:
        db_table = 'accounts_userprofile'
