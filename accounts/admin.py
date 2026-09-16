# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.conf import settings

from accounts.models import UserProfile
from archival_unit.models import ArchivalUnit


class UserProfileInlineForm(forms.ModelForm):
    """Limit unprocessed-series choices to the configured holding fonds."""

    class Meta:
        model = UserProfile
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['allowed_unprocessed_series'].queryset = ArchivalUnit.objects.filter(
            fonds=settings.UNPROCESSED_MATERIALS_FONDS,
            level='S',
        )


class UserProfileInline(admin.StackedInline):
    """
    Inline admin for the UserProfile model.

    Displays the user's assigned archival units on the built-in
    User admin page. Prevents deletion of the profile when
    editing a user and improves visibility of permissions.
    """
    model = UserProfile
    form = UserProfileInlineForm
    can_delete = False
    verbose_name_plural = 'User Profiles'
    filter_horizontal = ('allowed_archival_units', 'allowed_unprocessed_series')


# Define a new User admin
class UserAdmin(BaseUserAdmin):
    """
    Custom UserAdmin extended to show the related UserProfile inline.

    Adds management of:
        - Allowed archival units (ManyToMany)
        - Allowed unprocessed series (ManyToMany)
    while keeping Django's built-in User admin features.
    """
    inlines = (UserProfileInline,)


# Replace the default User admin with the customized version.
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
