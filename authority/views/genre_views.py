from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Genre
from authority.serializers import GenreSerializer, GenreSelectSerializer


class GenreList(generics.ListCreateAPIView):
    """
    Lists all genre authority records or creates a new one.

    GET:
        - Returns a searchable and orderable list of genres.

    POST:
        - Creates a new genre authority entry.
    """

    queryset = Genre.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['genre']
    search_fields = ('genre',)
    serializer_class = GenreSerializer


class GenreDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single genre authority record.

    GET:
        - Returns full genre details.

    PUT / PATCH:
        - Updates the genre record.

    DELETE:
        - Deletes the genre record if not referenced elsewhere.
    """

    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class GenreSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of genres for selection UIs.

    Features:
        - Alphabetical ordering
        - Searchable by genre label
        - Optimized for dropdowns and autocomplete widgets
    """

    serializer_class = GenreSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('genre',)
    queryset = Genre.objects.all().order_by('genre')
