from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Corporation
from authority.serializers import CorporationSerializer, CorporationSelectSerializer


class CorporationList(generics.ListCreateAPIView):
    """
    Lists all corporations or creates a new corporation authority record.

    GET:
        - Returns a searchable and orderable list of corporations.
        - Supports searching across:
            * canonical corporation name
            * alternative name formats

    POST:
        - Creates a new corporation record.
        - Supports nested writes for alternative name formats.
    """

    queryset = Corporation.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['name',]
    search_fields = ('name', 'corporationotherformat__name')
    serializer_class = CorporationSerializer


class CorporationDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single corporation record.

    GET:
        - Returns full corporation details.

    PUT / PATCH:
        - Updates corporation fields and nested alternative name formats.

    DELETE:
        - Removes the corporation record if not restricted elsewhere.
    """

    queryset = Corporation.objects.all()
    serializer_class = CorporationSerializer


class CorporationSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of corporations for selection UIs.

    Features:
        - Searchable by name and alternative name formats
        - Sorted alphabetically
        - Optimized for dropdowns and autocomplete widgets
    """

    serializer_class = CorporationSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('name', 'corporationotherformat__name')
    queryset = Corporation.objects.all().order_by('name')
