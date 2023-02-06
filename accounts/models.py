from django.contrib.auth.models import User
from django.db import models
from django.db.models.deletion import CASCADE

from archival_unit.models import ArchivalUnit


class UserProfile(models.Model):
    user = models.OneToOneField(User, unique=True, verbose_name='user', related_name='user_profile', on_delete=CASCADE)
    allowed_archival_units = models.ManyToManyField(ArchivalUnit, limit_choices_to={'level': 'S'}, blank=True)

    def assigned_archival_units(self):
        return self.allowed_archival_units.count()

    def __str__(self):
        return self.user.username

    class Meta:
        db_table = 'accounts_userprofile'
