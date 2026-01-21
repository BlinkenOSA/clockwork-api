from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import GeoRole
from controlled_list.serializers import GeoRoleSerializer, GeoRoleSelectSerializer


class GeoRoleList(generics.ListCreateAPIView):
    """
    Lists and creates geographic role entries.

    Geographic roles describe how a place or location is related to a record
    (e.g., place of creation, place depicted), enabling consistent indexing
    and display.
    """

    queryset = GeoRole.objects.all()
    serializer_class = GeoRoleSerializer


class GeoRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single geographic role entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = GeoRole.objects.all()
    serializer_class = GeoRoleSerializer


class GeoRoleSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of geographic role entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: role
        - Returns results ordered by role
    """

    serializer_class = GeoRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = GeoRole.objects.all().order_by('role')
