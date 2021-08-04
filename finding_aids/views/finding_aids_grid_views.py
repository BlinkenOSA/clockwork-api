from rest_framework import generics

from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_grid_serializers import FindingAidsGridSerializer


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