from rest_framework.generics import RetrieveAPIView, get_object_or_404

from catalog.serializers.finding_aids_entity_detail_serializer import FindingAidsEntityDetailSerializer
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityDetailView(RetrieveAPIView):
    permission_classes = []
    serializer_class = FindingAidsEntityDetailSerializer

    def get_object(self):
        catalog_id = self.kwargs['fa_entity_catalog_id']
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=catalog_id, published=True)
        return fa_entity
