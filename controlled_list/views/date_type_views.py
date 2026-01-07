from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import DateType
from controlled_list.serializers import DateTypeSerializer, DateTypeSelectSerializer


class DateTypeList(generics.ListCreateAPIView):
    """
    Lists and creates date type entries.

    Date types standardize how dates are interpreted in descriptive metadata
    (e.g., creation date, publication date, broadcast date).
    """

    queryset = DateType.objects.all()
    serializer_class = DateTypeSerializer


class DateTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single date type entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = DateType.objects.all()
    serializer_class = DateTypeSerializer


class DateTypeSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of date type entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: type
        - Returns results ordered by type
    """

    serializer_class = DateTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = DateType.objects.all().order_by('type')
