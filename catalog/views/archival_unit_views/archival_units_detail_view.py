"""
Archival unit detail and helper views for the public catalog.

These views provide read-only access to published ISAD(G) records
associated with archival units.

They intentionally expose different lookup mechanisms depending on
frontend use cases:
    - canonical archival unit ID lookup
    - lookup by full title for the hierarchical views quick detail
    - lightweight helper lookup by reference code

All views in this module:
    - are publicly accessible
    - only return published records
    - act as entry points into the catalog layer (not raw models)
"""

from rest_framework.generics import RetrieveAPIView, get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from catalog.serializers.archival_units_detail_serializer import ArchivalUnitsDetailSerializer, \
    ArchivalUnitsFacetQuerySerializer
from isad.models import Isad


class ArchivalUnitsDetailView(RetrieveAPIView):
    """
    Returns the full catalog detail view for a single archival unit.

    This view resolves an archival unit identifier to its corresponding
    published ISAD(G) record and serializes it for public catalog use.

    Lookup behavior:
        - Uses archival unit primary key
        - Enforces published=True
        - Returns 404 if no published ISAD exists

    This is the canonical archival unit detail endpoint used by
    the public catalog frontend.
    """

    permission_classes = []
    serializer_class = ArchivalUnitsDetailSerializer

    def get_object(self) -> Isad:
        """
        Resolves the requested archival unit ID to a published ISAD record.

        Returns:
            Published Isad instance associated with the archival unit.

        Raises:
            Http404 if no matching published record exists.
        """
        archival_unit_id = self.kwargs['archival_unit_id']
        isad = get_object_or_404(Isad, archival_unit__id=archival_unit_id, published=True)
        return isad


class ArchivalUnitsFacetQuickView(RetrieveAPIView):
    """
    Returns archival unit data based on a full title.

    This view supports quick access from archival unit hierarchical list where
    the frontend passes a human-readable full title rather than
    a stable identifier.

    Lookup behavior:
        - Parses reference code from the 'full_title' query parameter
        - Resolves the reference code to a published ISAD record
        - Returns 404 if parsing fails or no published record exists

    This endpoint exists primarily to bridge frontend facet navigation
    with canonical archival unit records.
    """

    permission_classes = []
    serializer_class = ArchivalUnitsFacetQuerySerializer

    def get_object(self) -> Isad:
        """
        Resolves a hierarchical list element provided full title to a published ISAD record.

        The expected 'full_title' format contains a reference code
        followed by a separator (e.g. "HU OSA 123 - Title").

        Returns:
            Published Isad instance associated with the reference code.

        Raises:
            Http404 if the reference code cannot be resolved.
        """

        archival_unit_full_title = self.request.query_params.get('full_title', None)
        parts = archival_unit_full_title.split(' - ')
        reference_code = parts[0].strip()
        isad = get_object_or_404(Isad, archival_unit__reference_code=reference_code, published=True)
        return isad


class ArchivalUnitsHelperView(APIView):
    """
    Lightweight helper endpoint for resolving archival unit reference codes.

    This view provides a minimal lookup service that maps a reference
    code to the corresponding catalog identifier.

    It is intended for:
        - internal linking
        - frontend routing helpers
        - legacy integrations

    The response is intentionally minimal to avoid over-fetching.
    """

    permission_classes = []

    def get(self, request, reference_code: str) -> Response:
        """
        Resolves a reference code to a catalog identifier.

        Args:
            reference_code:
                Reference code suffix (without "HU OSA" prefix).

        Returns:
            JSON response containing:
                - catalog_id: Public catalog identifier

        Raises:
            Http404 if no published record exists for the reference code.
        """

        isad = get_object_or_404(Isad, reference_code="HU OSA %s" % reference_code, published=True)
        return Response({'catalog_id': isad.catalog_id})

