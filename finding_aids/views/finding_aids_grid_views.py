from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_grid_serializers import FindingAidsGridSerializer
from drf_excel.mixins import XLSXFileMixin
from drf_excel.renderers import XLSXRenderer


class FindingAidsGridList(generics.ListAPIView):
    pagination_class = None
    serializer_class = FindingAidsGridSerializer

    def get_queryset(self):
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=False)\
                .order_by('container__container_no', 'folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsGridListExport(XLSXFileMixin, generics.ListAPIView):
    pagination_class = None
    serializer_class = FindingAidsGridSerializer
    renderer_classes = [XLSXRenderer]
    column_header = {
        'titles': [
            "ID", "Archival Reference Number",
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
        series_id = self.kwargs.get('series_id', None)
        try:
            archival_unit = ArchivalUnit.objects.get(id=series_id)
            return "%s.xlsx" % archival_unit.reference_code
        except ObjectDoesNotExist:
            return 'export.xlsx'

    def get_queryset(self):
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=False) \
                .order_by('container__container_no', 'folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()
