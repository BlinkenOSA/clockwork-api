from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Locale, Nationality
from controlled_list.serializers import (
    LocaleSerializer,
    LocaleSelectSerializer,
    NationalitySerializer,
    NationalitySelectSerializer,
)


class NationalityList(generics.ListCreateAPIView):
    """
    Lists and creates nationality entries.

    Nationality entries standardize how nationality is recorded for people
    or entities in descriptive metadata.
    """

    queryset = Nationality.objects.all()
    serializer_class = NationalitySerializer


class NationalityDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single nationality entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = Nationality.objects.all()
    serializer_class = NationalitySerializer


class NationalitySelectList(generics.ListAPIView):
    """
    Provides a lightweight list of nationality entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: nationality
        - Returns results ordered by nationality
    """

    serializer_class = NationalitySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('nationality',)
    queryset = Nationality.objects.all().order_by('nationality')
