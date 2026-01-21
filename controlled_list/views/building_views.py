from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Building
from controlled_list.serializers import BuildingSerializer, BuildingSelectSerializer


class BuildingList(generics.ListCreateAPIView):
    """
    Lists and creates building entries.

    Building entries represent standardized building names or identifiers
    used for location-based metadata and filtering.
    """

    queryset = Building.objects.all()
    serializer_class = BuildingSerializer


class BuildingDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single building entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = Building.objects.all()
    serializer_class = BuildingSerializer


class BuildingSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of building entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: building
        - Returns results ordered by building
    """

    serializer_class = BuildingSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('building',)
    queryset = Building.objects.all().order_by('building')
