from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import PrimaryType
from controlled_list.serializers import PrimaryTypeSerializer, PrimaryTypeSelectSerializer


class PrimaryTypeList(generics.ListCreateAPIView):
    """
    Lists and creates primary type entries.

    Primary types represent a short, standardized classification used for
    grouping and filtering records at a high level.
    """

    queryset = PrimaryType.objects.all()
    serializer_class = PrimaryTypeSerializer


class PrimaryTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single primary type entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = PrimaryType.objects.all()
    serializer_class = PrimaryTypeSerializer


class PrimaryTypeSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of primary type entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: type
        - Returns results ordered by type
    """

    serializer_class = PrimaryTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = PrimaryType.objects.all().order_by('type')
