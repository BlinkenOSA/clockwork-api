from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ExtentUnit
from controlled_list.serializers import ExtentUnitSerializer, ExtentUnitSelectSerializer


class ExtentUnitList(generics.ListCreateAPIView):
    """
    Lists and creates extent unit entries.

    Extent units standardize how physical or digital extent is expressed
    (e.g., pages, items, reels, gigabytes).
    """

    queryset = ExtentUnit.objects.all()
    serializer_class = ExtentUnitSerializer


class ExtentUnitDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single extent unit entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = ExtentUnit.objects.all()
    serializer_class = ExtentUnitSerializer


class ExtentUnitSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of extent unit entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: unit
        - Returns results ordered by unit
    """

    serializer_class = ExtentUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('unit',)
    queryset = ExtentUnit.objects.all().order_by('unit')
