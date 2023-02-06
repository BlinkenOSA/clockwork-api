from rest_framework.generics import RetrieveAPIView, get_object_or_404

from catalog.serializers.archival_units_tree_quick_view_serializer import ArchivalUnitsTreeQuickViewSerializer
from isad.models import Isad


class ArchivalUnitsTreeQuickView(RetrieveAPIView):
    permission_classes = []
    serializer_class = ArchivalUnitsTreeQuickViewSerializer

    def get_object(self):
        archival_unit_id = self.kwargs['archival_unit_id']
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)
        return isad
