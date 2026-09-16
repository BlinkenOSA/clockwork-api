from django.conf import settings


UNPROCESSED_MATERIALS_GROUP = 'Unprocessed Materials'


def is_unprocessed_series(archival_unit) -> bool:
    """Return whether an archival unit is a series in the holding fonds."""
    return bool(
        archival_unit and
        archival_unit.level == 'S' and
        archival_unit.fonds == settings.UNPROCESSED_MATERIALS_FONDS
    )


def can_access_unprocessed_series(user, archival_unit) -> bool:
    """Check group membership and the user's optional unprocessed allowlist."""
    if not user or not user.is_authenticated or not is_unprocessed_series(archival_unit):
        return False
    if user.is_superuser:
        return True
    if not user.groups.filter(name=UNPROCESSED_MATERIALS_GROUP).exists():
        return False
    allowed_series = user.user_profile.allowed_unprocessed_series
    if not allowed_series.exists():
        return True
    return allowed_series.filter(pk=archival_unit.pk).exists()


def accessible_unprocessed_series(user):
    """Return the unprocessed series visible to a user."""
    from archival_unit.models import ArchivalUnit

    queryset = ArchivalUnit.objects.filter(
        fonds=settings.UNPROCESSED_MATERIALS_FONDS,
        level='S',
    )
    if user and user.is_authenticated and user.is_superuser:
        return queryset
    if not user or not user.is_authenticated:
        return queryset.none()
    if not user.groups.filter(name=UNPROCESSED_MATERIALS_GROUP).exists():
        return queryset.none()
    allowed_series = user.user_profile.allowed_unprocessed_series
    if not allowed_series.exists():
        return queryset
    return queryset.filter(pk__in=allowed_series.values('pk'))
