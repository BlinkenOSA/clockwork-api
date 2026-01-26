from rest_framework import permissions

from container.models import Container


class AllowedArchivalUnitPermission(permissions.BasePermission):
    """
    Permission class for restricting access to archival units.

    This permission enforces per-user access control based on the
    `allowed_archival_units` relation defined in the user's profile.

    It ensures that users can only perform operations on archival
    units that they have been explicitly granted access to.

    The permission is applied at both:

        - View level (has_permission)
        - Object level (has_object_permission)

    Typical use cases:
        - Protecting ISAD records
        - Restricting container operations
        - Limiting finding aids access
        - Enforcing archival hierarchy permissions

    Expected Dependencies:
        - request.user.user_profile.allowed_archival_units (ManyToMany)
        - Container.archival_unit relationship

    Error Message:
        Returned when permission is denied:
            "You are not allowed to do actions with this Archival Unit."
    """

    message = 'You are not allowed to do actions with this Archival Unit.'

    def has_permission(self, request, view):
        """
        Perform permission checks at the view level.

        This method is primarily used for endpoints where the archival
        unit is identified via URL parameters (e.g., container_id).

        Special handling is applied for the `finding_aids-v1` API version,
        where the container ID is used to resolve the related archival unit.

        Args:
            request (HttpRequest):
                Incoming HTTP request.

            view (APIView):
                Target view instance.

        Returns:
            bool:
                True if the user is authorized, False otherwise.
        """
        user = request.user

        # If the user has restricted archival units
        if user.user_profile.allowed_archival_units.exists():

            # Special handling for Finding Aids API v1
            if request.version == 'finding_aids-v1':

                if 'container_id' in view.kwargs:
                    container_id = view.kwargs['container_id']

                    container = Container.objects.get(id=container_id)

                    return user.user_profile.allowed_archival_units.filter(
                        id=container.archival_unit.id
                    ).exists()

        # If no restrictions apply
        return True

    def has_object_permission(self, request, view, obj):
        """
        Perform permission checks at the object level.

        This method is invoked for endpoints that directly operate
        on model instances.

        The permission is evaluated by verifying whether the object's
        associated archival unit is included in the user's allowed set.

        Args:
            request (HttpRequest):
                Incoming HTTP request.

            view (APIView):
                Target view instance.

            obj (models.Model):
                Target model instance.

        Returns:
            bool:
                True if access is permitted, False otherwise.
        """
        user = request.user

        # If the user has restricted archival units
        if user.user_profile.allowed_archival_units.exists():

            return user.user_profile.allowed_archival_units.filter(
                pk=obj.archival_unit.id
            ).exists()

        # If the user has unrestricted access
        return True
