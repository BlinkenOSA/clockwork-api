from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import CarrierType
from controlled_list.serializers import CarrierTypeSerializer, CarrierTypeSelectSerializer


class CarrierTypeList(generics.ListCreateAPIView):
    """
    Lists and creates carrier type entries.

    Carrier types describe the physical or technical format of containers
    and may include dimensional metadata used for storage and labeling.
    """

    queryset = CarrierType.objects.all()
    serializer_class = CarrierTypeSerializer


class CarrierTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single carrier type entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = CarrierType.objects.all()
    serializer_class = CarrierTypeSerializer


class CarrierTypeSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of carrier type entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: type
        - Returns results ordered by type
    """

    serializer_class = CarrierTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = CarrierType.objects.all().order_by('type')
