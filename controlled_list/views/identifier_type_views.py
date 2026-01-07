from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import IdentifierType
from controlled_list.serializers import IdentifierTypeSerializer, IdentifierTypeSelectSerializer


class IdentifierTypeList(generics.ListCreateAPIView):
    """
    Lists and creates identifier type entries.

    Identifier types define the meaning or scheme of identifiers used in
    records (e.g., internal identifier, legacy identifier, external standard).
    """

    queryset = IdentifierType.objects.all()
    serializer_class = IdentifierTypeSerializer


class IdentifierTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single identifier type entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = IdentifierType.objects.all()
    serializer_class = IdentifierTypeSerializer


class IdentifierTypeSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of identifier type entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: type
        - Returns results ordered by type
    """

    serializer_class = IdentifierTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = IdentifierType.objects.all().order_by('type')
