"""
Statistics endpoint for retrieving collection-specific keyword tags.

This module exposes a read-only API endpoint that returns a small,
randomized selection of keywords associated with published
finding aids entities.

The result is typically used for:
    - tag clouds
    - discovery prompts
    - homepage or collection overview widgets
"""

from rest_framework.response import Response
from rest_framework.views import APIView

from controlled_list.models import Keyword


class CollectionSpecificTags(APIView):
    """
    Returns a randomized list of collection-specific keyword tags.

    The keywords are derived exclusively from published finding aids
    entities and are intended to highlight themes or subjects
    present in the collection.

    The response:
        - contains at most 10 unique keyword strings
        - is randomly ordered on each request
        - contains no additional metadata
    """

    permission_classes = []

    def get(self, *args, **kwargs) -> Response:
        """
        Retrieves a randomized subset of keywords used in the collection.

        Selection criteria:
            - keyword must be associated with at least one published
              finding aids entity
            - keywords are randomized at the database level
            - duplicate string values are filtered out manually

        Returns:
            A list of up to 10 keyword strings.
        """
        keywords = []
        for keyword in Keyword.objects.filter(
            findingaidsentity__published=True
        ).order_by('?').distinct():
            if len(keywords) < 10:
                if str(keyword) not in keywords:
                    keywords.append(str(keyword))
        return Response(keywords)