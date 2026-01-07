from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Keyword
from controlled_list.serializers import KeywordSerializer, KeywordSelectSerializer


class KeywordList(generics.ListCreateAPIView):
    """
    Lists and creates keyword entries.

    Keywords provide standardized descriptive terms for tagging and discovery.
    This endpoint supports searching over keyword text to aid administration
    and reuse.

    Search behavior:
        - Uses DRF SearchFilter
        - Searches over: keyword
    """

    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer
    filter_backends = (SearchFilter,)
    search_fields = ('keyword',)


class KeywordDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single keyword entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class KeywordSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of keyword entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: keyword
        - Returns results ordered by keyword
    """

    serializer_class = KeywordSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('keyword',)
    queryset = Keyword.objects.all().order_by('keyword')
