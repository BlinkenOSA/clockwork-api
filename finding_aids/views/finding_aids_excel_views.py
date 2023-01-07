from rest_framework.generics import get_object_or_404
from rest_framework.views import APIView
from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class FindingAidsExcelExport(APIView):
    def get(self, request, *args, **kwargs):
        series = get_object_or_404(ArchivalUnit, pk=self.kwargs.get('series_id', None))
        fa_entities = FindingAidsEntity.objects.filter(archival_unit=series).order_by('container_no', 'sequence_no')

