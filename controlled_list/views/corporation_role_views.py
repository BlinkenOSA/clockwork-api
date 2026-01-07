from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import CorporationRole
from controlled_list.serializers import CorporationRoleSerializer, CorporationRoleSelectSerializer


class CorporationRoleList(generics.ListCreateAPIView):
    """
    Lists and creates corporation role entries.

    Corporation roles describe how a corporate entity is related to a record
    (e.g., creator, contributor, subject), enabling consistent indexing and display.
    """

    queryset = CorporationRole.objects.all()
    serializer_class = CorporationRoleSerializer


class CorporationRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single corporation role entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = CorporationRole.objects.all()
    serializer_class = CorporationRoleSerializer


class CorporationRoleSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of corporation role entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: role
        - Returns results ordered by role
    """

    serializer_class = CorporationRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = CorporationRole.objects.all().order_by('role')
