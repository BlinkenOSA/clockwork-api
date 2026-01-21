from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import AccessRight
from controlled_list.serializers import AccessRightSerializer, AccessRightSelectSerializer


class AccessRightList(generics.ListCreateAPIView):
    """
    Lists and creates access right statements.

    This endpoint supports controlled vocabulary administration and includes
    search over the statement text.

    Search behavior:
        - Uses DRF SearchFilter
        - Searches over: statement

    Ordering:
        - Supports ordering by: statement
    """

    queryset = AccessRight.objects.all()
    serializer_class = AccessRightSerializer
    filter_backends = [SearchFilter]
    search_fields = ['statement']
    ordering_fields = ['statement']


class AccessRightDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single access right statement.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = AccessRight.objects.all()
    serializer_class = AccessRightSerializer


class AccessRightSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of access right statements for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over the statement text
        - Returns results ordered by statement
    """

    serializer_class = AccessRightSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('statement',)
    queryset = AccessRight.objects.all().order_by('statement')
