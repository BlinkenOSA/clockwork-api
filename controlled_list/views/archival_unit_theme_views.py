from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ArchivalUnitTheme
from controlled_list.serializers import ArchivalUnitThemeSerializer, ArchivalUnitThemeSelectSerializer


class ArchivalUnitThemeList(generics.ListCreateAPIView):
    """
    Lists and creates archival unit theme entries.

    Archival unit themes provide a standardized way to categorize archival
    units for browsing, filtering, and discovery.
    """

    queryset = ArchivalUnitTheme.objects.all()
    serializer_class = ArchivalUnitThemeSerializer


class ArchivalUnitThemeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single archival unit theme entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = ArchivalUnitTheme.objects.all()
    serializer_class = ArchivalUnitThemeSerializer


class ArchivalUnitThemeSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of archival unit theme entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: theme
        - Returns results ordered by theme
    """

    serializer_class = ArchivalUnitThemeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('theme',)
    queryset = ArchivalUnitTheme.objects.all().order_by('theme')
