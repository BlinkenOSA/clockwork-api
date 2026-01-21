from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Locale
from controlled_list.serializers import LocaleSerializer, LocaleSelectSerializer


class LocaleList(generics.ListCreateAPIView):
    """
    Lists and creates locale entries.

    Locales represent standardized language or locale codes paired with a
    human-readable display name. Locale entries use a short string primary key.
    """

    queryset = Locale.objects.all()
    serializer_class = LocaleSerializer


class LocaleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single locale entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = Locale.objects.all()
    serializer_class = LocaleSerializer


class LocaleSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of locale entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: locale_name
        - Returns results ordered by locale_name
    """

    serializer_class = LocaleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('locale_name',)
    queryset = Locale.objects.all().order_by('locale_name')
