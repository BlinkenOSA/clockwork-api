from archival_unit.models import ArchivalUnit


class ListAllowedArchivalUnitMixin:
    """
    Mixin for restricting archival unit querysets based on user permissions.

    This mixin limits the returned fonds-level archival units according
    to the user's assigned access scope.

    If the user has explicitly assigned archival units in their profile,
    only fonds belonging to those units are returned.

    If no restrictions exist, all fonds-level archival units are returned.

    Intended use:
        Applied to ListAPIView-based views that expose fonds-level
        archival units in selection lists and dropdowns.

    Expected dependencies:
        - request.user.user_profile.allowed_archival_units (ManyToMany)

    Behavior:
        - Restricted users → filtered fonds list
        - Unrestricted users → full fonds list
    """

    def get_queryset(self):
        """
        Build a queryset of permitted fonds-level archival units.

        The method inspects the current user's profile and determines
        whether access restrictions apply.

        Returns:
            QuerySet[ArchivalUnit]:
                Fonds-level archival units the user is allowed to access.
        """
        user = self.request.user

        # If the user has restricted archival units assigned
        if user.user_profile.allowed_archival_units.exists():

            queryset = ArchivalUnit.objects.none()

            # Build a union of permitted fonds
            for archival_unit in user.user_profile.allowed_archival_units.all():
                queryset |= ArchivalUnit.objects.filter(
                    fonds=archival_unit.fonds,
                    level='F'
                )

            return queryset

        # If the user has no restrictions
        return ArchivalUnit.objects.filter(level='F')
