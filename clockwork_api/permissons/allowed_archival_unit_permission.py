from rest_framework import permissions


class AllowedArchivalUnitPermission(permissions.BasePermission):
    message = 'You are not allowed to do actions with this Archival Unit.'

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_profile.allowed_archival_units.count() > 0:
            return user.user_profile.allowed_archival_units.filter(pk=obj.archival_unit.id).exists()
        return True
