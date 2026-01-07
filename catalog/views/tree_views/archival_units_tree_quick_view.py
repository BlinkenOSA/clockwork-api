"""
Lightweight archival unit tree view for the public catalog.

This module provides a simplified, read-only tree representation
of an archival unit hierarchy.

Unlike the full tree view, this endpoint is optimized for:
    - fast loading
    - preview or summary displays
    - UI components that do not require the complete hierarchy

The actual tree structure and depth are controlled by the serializer.
"""
from rest_framework.generics import RetrieveAPIView, get_object_or_404

from catalog.serializers.archival_units_tree_quick_view_serializer import ArchivalUnitsTreeQuickViewSerializer
from isad.models import Isad


class ArchivalUnitsTreeQuickView(RetrieveAPIView):
    """
    Returns a lightweight archival unit tree for quick UI rendering.

    This view resolves an archival unit identifier to its published
    ISAD(G) record and delegates tree construction entirely to a
    specialized serializer.

    Design decisions:
        - Uses ISAD as the entry point, not ArchivalUnit
        - Enforces published=True
        - Keeps view logic minimal for performance and clarity

    This endpoint is typically used for:
        - tree previews
        - sidebar navigation
        - initial UI loads before full tree expansion
    """

    permission_classes = []
    serializer_class = ArchivalUnitsTreeQuickViewSerializer

    def get_object(self) -> Isad:
        """
        Resolves the archival unit ID to a published ISAD record.

        Returns:
            Published Isad instance associated with the archival unit.

        Raises:
            Http404 if no published ISAD exists for the given archival unit.
        """
        archival_unit_id = self.kwargs['archival_unit_id']
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)
        return isad
