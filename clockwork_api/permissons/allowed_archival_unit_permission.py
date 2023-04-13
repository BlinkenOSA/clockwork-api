from rest_framework import permissions

from container.models import Container


class AllowedArchivalUnitPermission(permissions.BasePermission):
    message = 'You are not allowed to do actions with this Archival Unit.'

    def has_permission(self, request, view):
        user = request.user
        if user.user_profile.allowed_archival_units.count() > 0:
            if request.version == 'finding_aids-v1':
                if 'container_id' in view.kwargs:
                    container_id = view.kwargs['container_id']
                    container = Container.objects.get(id=container_id)
                    return user.user_profile.allowed_archival_units.filter(id=container.archival_unit.id).exists()
        return True

    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.user_profile.allowed_archival_units.count() > 0:
            return user.user_profile.allowed_archival_units.filter(pk=obj.archival_unit.id).exists()
        return True
