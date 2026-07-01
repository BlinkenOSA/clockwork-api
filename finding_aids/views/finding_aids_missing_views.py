from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from rest_framework.filters import SearchFilter

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSelectSerializer
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityListSerializer


class FindingAidsMissingList(generics.ListAPIView):
    """
    Lists all non-template finding aids entities currently marked as missing.

    Intended for reporting or review screens that need a consolidated list of
    folders/items previously described but now flagged missing.
    """

    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ('title', 'title_original')
    serializer_class = FindingAidsEntityListSerializer

    def get_queryset(self):
        """
        Returns all missing non-template entities ordered for stable display.
        """
        return FindingAidsEntity.objects.filter(
            is_template=False,
            missing=True
        ).order_by(
            'archival_unit__fonds',
            'archival_unit__subfonds',
            'archival_unit__series',
            'container__container_no',
            'folder_no',
            'sequence_no'
        )

    def filter_queryset(self, queryset):
        """
        Applies query-parameter filtering to the base queryset.

        Supported filters:
            - archival_unit_id: exact series/archival unit primary key
        """
        qs = queryset

        archival_unit_id = self.request.query_params.get('archival_unit_id', None)
        if archival_unit_id:
            qs = qs.filter(archival_unit_id=archival_unit_id)

        return super().filter_queryset(qs)


class FindingAidsMissingArchivalUnitSelectList(generics.ListAPIView):
    """
    Lists series archival units that contain missing finding aids entities.

    Intended for select/dropdown UI components used to scope missing-record
    reporting to a specific series.
    """

    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ['title', 'reference_code']

    def get_queryset(self):
        """
        Returns series units that have at least one non-template missing entity.
        """
        return ArchivalUnit.objects.filter(
            level='S',
            findingaidsentity__missing=True,
            findingaidsentity__is_template=False
        ).distinct().order_by('fonds', 'subfonds', 'series')
