from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Place
from authority.serializers import PlaceSerializer, PlaceSelectSerializer


class PlaceList(generics.ListCreateAPIView):
    """
    Lists all place authority records or creates a new one.

    GET:
        - Returns a searchable and orderable list of places.

    POST:
        - Creates a new place authority record.
    """

    queryset = Place.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['place']
    search_fields = ('place',)
    serializer_class = PlaceSerializer


class PlaceDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single place authority record.

    GET:
        - Returns full place details.

    PUT / PATCH:
        - Updates the place record.

    DELETE:
        - Deletes the place record if not referenced elsewhere.
    """

    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class PlaceSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of places for selection UIs.

    Features:
        - Alphabetical ordering
        - Searchable by place name
        - Optimized for dropdowns and autocomplete widgets
    """

    serializer_class = PlaceSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('place',)
    queryset = Place.objects.all().order_by('place')
