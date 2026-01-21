from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_grid_serializers import FindingAidsGridSerializer
from drf_excel.mixins import XLSXFileMixin
from drf_excel.renderers import XLSXRenderer


class FindingAidsGridList(generics.ListAPIView):
    """
    Returns finding aids entities in a "grid" (spreadsheet-like) shape.

    This endpoint is intended for frontends that display records in an
    Excel-style editable table. It uses FindingAidsGridSerializer, which
    exposes a curated subset of fields suitable for inline editing.

    Queryset behavior:
        - filters by archival unit (series_id)
        - excludes templates
        - orders records by container number, folder number, and sequence number
          to match physical/intellectual arrangement.
    """

    pagination_class = None
    serializer_class = FindingAidsGridSerializer

    def get_queryset(self):
        """
        Returns ordered entities for the given archival unit series.

        URL kwargs:
            series_id: archival_unit id used to filter entities

        Returns:
            QuerySet[FindingAidsEntity]: filtered and ordered, or empty if no series_id.
        """
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=False)\
                .order_by('container__container_no', 'folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsGridListExport(XLSXFileMixin, generics.ListAPIView):
    """
    Exports finding aids entities as an XLSX file for Excel-style workflows.

    Uses drf-excel:
        - XLSXFileMixin for file handling
        - XLSXRenderer to render the response as a spreadsheet

    Output:
        - The spreadsheet columns and header styling are defined in `column_header`
        - Row style defaults are defined in `body`

    Queryset behavior matches FindingAidsGridList:
        - filters by archival unit (series_id)
        - excludes templates
        - orders by container/folder/sequence
    """

    pagination_class = None
    serializer_class = FindingAidsGridSerializer
    renderer_classes = [XLSXRenderer]
    column_header = {
        'titles': [
            "ID", "Legacy ID", "Archival Reference Number",
            "Title", "Title (Original)", "Locale",
            "Contents Summary", "Contents Summary (Original)",
            "Date (from)", "Date (to)", "Start Time", "End Time",
            "Note", "Note (Original)"
        ],
        'height': 20,
        'style': {
            'alignment': {
                'shrink_to_fit': True,
            },
            'fill': {
                'fill_type': 'solid',
                'start_color': 'FF333333',
            },
            'font': {
                'bold': True,
                'color': 'FFFFFFFF',
            },
        }
    }
    body = {
        'style': {
            'alignment': {
                'shrink_to_fit': True,
                'wrapText': True
            }
        },
    }

    def get_filename(self, request, *args, **kwargs):
        """
        Determines the exported XLSX filename.

        Preference order:
            1. "<archival_unit.reference_code>.xlsx" if the archival unit exists
            2. "export.xlsx" fallback when the archival unit cannot be loaded

        Returns:
            str: filename used by XLSXFileMixin.
        """
        series_id = self.kwargs.get('series_id', None)
        try:
            archival_unit = ArchivalUnit.objects.get(id=series_id)
            return "%s.xlsx" % archival_unit.reference_code
        except ObjectDoesNotExist:
            return 'export.xlsx'

    def get_queryset(self):
        """
        Returns ordered entities for export for the given archival unit series.

        URL kwargs:
            series_id: archival_unit id used to filter entities

        Returns:
            QuerySet[FindingAidsEntity]: filtered and ordered, or empty if no series_id.
        """
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=False) \
                .order_by('container__container_no', 'folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()
