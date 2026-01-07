"""
Statistics endpoint for calculating archival unit sizes.

This module exposes a read-only API endpoint that returns the size of each
top-level archival unit (fonds), measured by the number of published
finding aids entities it contains.

The size metric is used for:
    - public catalog statistics
    - collection overview pages
    - comparative visualizations
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSizes(APIView):
    """
    Returns size statistics for top-level archival units (fonds).

    Each fonds is represented with:
        - its reference code
        - its title
        - the total number of published finding aids entities
          belonging to that fonds

    Size is calculated by counting all published finding aids entities
    whose archival unit belongs to the fonds (via subfonds and series).
    """

    def get(self, *args, **kwargs) -> Response:
        """
        Computes and returns archival unit size statistics.

        Returns:
            A list of dictionaries, each containing:
                - reference_code: Fonds reference code
                - title: Fonds title
                - size: Number of published finding aids entities
        """
        archival_unit_sizes = []
        for archival_unit in ArchivalUnit.objects.filter(
            level='F',
            isad__published=True
        ).all():
            au = {}
            au['reference_code'] = archival_unit.reference_code
            au['title'] = archival_unit.title
            au['size'] = FindingAidsEntity.objects.filter(
                archival_unit__parent__parent=archival_unit,
                published=True
            ).count()
            archival_unit_sizes.append(au)
        return Response(archival_unit_sizes)