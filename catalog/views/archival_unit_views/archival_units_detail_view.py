from rest_framework.generics import RetrieveAPIView, get_object_or_404

from catalog.serializers.archival_units_detail_serializer import ArchivalUnitsDetailSerializer
from isad.models import Isad


class ArchivalUnitsDetailView(RetrieveAPIView):
    permission_classes = []
    serializer_class = ArchivalUnitsDetailSerializer

    def get_object(self):
        archival_unit_id = self.kwargs['archival_unit_id']
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)
        return isad
