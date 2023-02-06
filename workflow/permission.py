from django.contrib.auth.models import Group
from rest_framework.permissions import BasePermission


class APIGroupPermission(BasePermission):

    group_name = "Api"

    def has_permission(self, request, view):
        """
        Should simply return, or raise a 403 response.
        """
        try:
            user = request.user
            return user.groups.filter(name=self.group_name).exists()
        except Group.DoesNotExist:
            return None
