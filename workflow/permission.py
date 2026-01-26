from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission


class APIGroupPermission(BasePermission):
    """
    Permission class restricting access to users in a specific Django group.

    This permission is intended for internal / automation-facing endpoints used
    by long-term preservation workflow scripts.

    By default, access is granted only to users who belong to the Django auth
    group named ``"Api"``.
    """

    group_name = "Api"

    def has_permission(self, request, view):
        """
        Checks whether the requesting user belongs to the configured group.

        Args:
            request: DRF request object.
            view: DRF view instance.

        Returns:
            bool: True if the user is a member of ``group_name``, otherwise False.

        Notes:
            - ``Group.DoesNotExist`` is unlikely to be raised by the underlying
              queryset filter call; it is kept for defensive compatibility with
              older patterns.
            - Returning ``None`` is treated as a falsy value by DRF permission
              handling.
        """
        try:
            user = request.user
            return user.groups.filter(name=self.group_name).exists()
        except Group.DoesNotExist:
            return None
