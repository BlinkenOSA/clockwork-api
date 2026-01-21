from rest_framework.generics import ListAPIView

from accession.models import Accession
from archival_unit.models import ArchivalUnit
from container.models import Container
from dashboard.serializers.log_serializers import (
    AccessionLogSerializer,
    ArchivalUnitLogSerializer,
    IsadLogSerializer,
    FindingAidsLogSerializer,
    DigitizationLogSerializer,
)
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class AccessionLog(ListAPIView):
    """
    Returns recent accession activity for the dashboard.

    Displays the most recent accessions with transfer information,
    ordered by transfer date and sequence number.
    """

    queryset = (
        Accession.objects
        .filter(transfer_date__isnull=False)
        .order_by('-transfer_date', '-seq')
        .all()[:20]
    )
    serializer_class = AccessionLogSerializer
    pagination_class = None


class ArchivalUnitLog(ListAPIView):
    """
    Returns recently created archival units for the dashboard.

    Results are ordered by creation date, with secondary ordering
    to maintain hierarchical consistency.
    """

    queryset = (
        ArchivalUnit.objects
        .filter(date_created__isnull=False)
        .order_by('-date_created', 'fonds', 'subfonds', 'series')
        .all()[:20]
    )
    serializer_class = ArchivalUnitLogSerializer
    pagination_class = None


class IsadCreateLog(ListAPIView):
    """
    Returns recently created ISAD(G) descriptions.

    Used by the dashboard to display recent descriptive activity.
    """

    queryset = (
        Isad.objects
        .filter(date_created__isnull=False)
        .order_by('-date_created')
        .all()[:20]
    )
    serializer_class = IsadLogSerializer
    pagination_class = None


class IsadUpdateLog(ListAPIView):
    """
    Returns recently updated ISAD(G) descriptions.

    Used by the dashboard to highlight recent edits to descriptive records.
    """

    queryset = (
        Isad.objects
        .filter(date_updated__isnull=False)
        .order_by('-date_updated')
        .all()[:20]
    )
    serializer_class = IsadLogSerializer
    pagination_class = None


class FindingAidsCreateLog(ListAPIView):
    """
    Returns recently created finding aids.

    Used by the dashboard to surface new finding-aid entities.
    """

    queryset = (
        FindingAidsEntity.objects
        .filter(date_created__isnull=False)
        .order_by('-date_created')
        .all()[:20]
    )
    serializer_class = FindingAidsLogSerializer
    pagination_class = None


class FindingAidsUpdateLog(ListAPIView):
    """
    Returns recently updated finding aids.

    Used by the dashboard to surface recent changes to finding-aid entities.
    """

    queryset = (
        FindingAidsEntity.objects
        .filter(date_updated__isnull=False)
        .order_by('-date_updated')
        .all()[:20]
    )
    serializer_class = FindingAidsLogSerializer
    pagination_class = None


class DigitizationLog(ListAPIView):
    """
    Returns recent digitization activity.

    Displays containers for which a digital version has been created,
    ordered by digitization date and container reference.
    """

    queryset = (
        Container.objects
        .filter(digital_version_creation_date__isnull=False)
        .order_by(
            '-digital_version_creation_date',
            'archival_unit__reference_code',
            'container_no',
        )
        .all()[:20]
    )
    serializer_class = DigitizationLogSerializer
    pagination_class = None
