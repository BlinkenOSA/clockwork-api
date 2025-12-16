"""
Finding aids entity detail view for the public catalog.

This module provides read-only access to a single published finding aids
entity using its public catalog identifier.

The endpoint is designed for direct consumption by the catalog frontend
and external clients, returning a fully serialized representation of
the finding aids entity.
"""

from rest_framework.generics import RetrieveAPIView, get_object_or_404

from catalog.serializers.finding_aids_entity_detail_serializer import FindingAidsEntityDetailSerializer
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityDetailView(RetrieveAPIView):
    """
    Returns the full public catalog representation of a finding aids entity.

    This view resolves a catalog-facing identifier to a published
    FindingAidsEntity record and serializes it using a catalog-specific
    serializer.

    Design decisions:
        - Lookup is performed via catalog_id, not primary key
        - Only published entities are exposed
        - The response is read-only and publicly accessible

    This endpoint is typically used when navigating directly to a
    finding aids record from the public catalog UI.
    """

    permission_classes = []
    serializer_class = FindingAidsEntityDetailSerializer

    def get_object(self) -> FindingAidsEntity:
        """
        Resolves the catalog identifier to a published finding aids entity.

        Returns:
            Published FindingAidsEntity instance.

        Raises:
            Http404 if no published entity exists for the given catalog ID.
        """

        catalog_id = self.kwargs['fa_entity_catalog_id']
        fa_entity = get_object_or_404(FindingAidsEntity, catalog_id=catalog_id, published=True)
        return fa_entity
