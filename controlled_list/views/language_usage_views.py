from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import LanguageUsage
from controlled_list.serializers import LanguageUsageSerializer, LanguageUsageSelectSerializer


class LanguageUsageList(generics.ListCreateAPIView):
    """
    Lists and creates language usage entries.

    Language usage values describe how a language is used in a record
    (e.g., spoken, written, subtitles), supporting consistent description
    and filtering.
    """

    queryset = LanguageUsage.objects.all()
    serializer_class = LanguageUsageSerializer


class LanguageUsageDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single language usage entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = LanguageUsage.objects.all()
    serializer_class = LanguageUsageSerializer


class LanguageUsageSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of language usage entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: usage
        - Returns results ordered by usage
    """

    serializer_class = LanguageUsageSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('usage',)
    queryset = LanguageUsage.objects.all().order_by('usage')
