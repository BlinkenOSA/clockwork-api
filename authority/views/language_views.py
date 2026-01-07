from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Language
from authority.serializers import LanguageSerializer, LanguageSelectSerializer


class LanguageList(generics.ListCreateAPIView):
    """
    Lists all language authority records or creates a new one.

    GET:
        - Returns a searchable and orderable list of languages.
        - Supports searching by:
            * language name
            * ISO 639-2 code
            * ISO 639-3 code

    POST:
        - Creates a new language authority record.
    """

    queryset = Language.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['language', 'iso_639_2', 'iso_639_3']
    search_fields = ('language', 'iso_639_2', 'iso_639_3')
    serializer_class = LanguageSerializer


class LanguageDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single language authority record.

    GET:
        - Returns full language details.

    PUT / PATCH:
        - Updates the language record.

    DELETE:
        - Deletes the language record if not referenced elsewhere.
    """

    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class LanguageSelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of languages for selection UIs.

    Features:
        - Alphabetical ordering
        - Searchable by language name
        - Optimized for dropdowns and autocomplete components
    """

    serializer_class = LanguageSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('language',)
    queryset = Language.objects.all().order_by('language')
