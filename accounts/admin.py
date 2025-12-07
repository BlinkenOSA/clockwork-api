# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from accounts.models import UserProfile


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for the UserProfile model.

    Displays the user's assigned archival units on the built-in
    User admin page. Prevents deletion of the profile when
    editing a user and improves visibility of permissions.
    """
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'
    filter_horizontal = ('allowed_archival_units',)


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin extended to show the related UserProfile inline.

    Adds management of:
        - Allowed archival units (ManyToMany)
    while keeping Django's built-in User admin features.
    """
    inlines = (UserProfileInline,)


# Replace the default User admin with the customized version.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
