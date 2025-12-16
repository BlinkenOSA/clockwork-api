"""
Statistics endpoint for retrieving recently added or published catalog content.

This module provides a public API endpoint used by the catalog frontend
to display newly added archival descriptions or series based on
publication date.

The returned content depends on the requested content type and applies
different aggregation rules accordingly.
"""

import datetime

from rest_framework.response import Response
from rest_framework.views import APIView

from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class NewlyAddedContent(APIView):
    """
    Returns recently published catalog content.

    The behavior of this endpoint depends on the `content_type` URL parameter:

    - `isad`:
        Returns the 5 most recently published ISAD descriptions
        at series level (`description_level = 'S'`).

    - any other value (e.g. 'folder'):
        Returns up to 5 distinct archival series that have had
        finding aids published within the last two years.

    This endpoint is primarily used for:
        - "Newly added content" widgets
        - catalog landing pages
        - discovery and promotional features
    """

    permission_classes = []

    def get(self, *args, **kwargs) -> Response:
        """
        Retrieves newly added or recently published content.

        URL parameters:
           content_type (str):
               Determines which publication logic to apply.
               Expected values:
                   - 'isad'
                   - any other value (treated as finding aids based)

        Returns:
           A list of dictionaries containing:
               - id: catalog identifier
               - reference_code: archival reference code
               - title: full archival unit title
               - date_published: publication date
        """
        response = []
        if kwargs['content_type'] == 'isad':
            for isad in Isad.objects.filter(
                description_level='S',
                published=True
            ).order_by(
                '-date_published'
            ).all()[:5]:
                response.append({
                    'id': isad.catalog_id,
                    'reference_code': isad.reference_code,
                    'title': isad.archival_unit.title_full,
                    'date_published': isad.date_published
                })
        else:
            added_series = []
            for finding_aids in FindingAidsEntity.objects.select_related('archival_unit').filter(
                published=True,
                date_published__year__gt=datetime.datetime.now().year-2
            ).order_by(
                '-date_published'
            ).all():
                if len(added_series) == 5:
                    break
                if finding_aids.archival_unit.id not in added_series:
                    response.append({
                        'id': finding_aids.archival_unit.isad.catalog_id,
                        'reference_code': finding_aids.archival_unit.reference_code,
                        'title': finding_aids.archival_unit.title_full,
                        'date_published': finding_aids.date_published
                    })
                    added_series.append(finding_aids.archival_unit.id)
        return Response(response)
