from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import RightsRestrictionReason
from controlled_list.serializers import (
    RightsRestrictionReasonSerializer,
    RightsRestrictionReasonSelectSerializer,
)


class RightsRestrictionReasonList(generics.ListCreateAPIView):
    """
    Lists and creates rights restriction reason entries.

    Rights restriction reasons standardize explanations for why access
    or use of materials is limited (e.g., privacy, legal, donor agreement).
    """

    queryset = RightsRestrictionReason.objects.all()
    serializer_class = RightsRestrictionReasonSerializer


class RightsRestrictionReasonDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single rights restriction reason entry.

    This endpoint is intended for controlled vocabulary maintenance
    workflows and uses the full serializer representation.
    """

    queryset = RightsRestrictionReason.objects.all()
    serializer_class = RightsRestrictionReasonSerializer


class RightsRestrictionReasonSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of rights restriction reason entries for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation
        - Disables pagination
        - Supports search over: reason
        - Returns results ordered by reason
    """

    serializer_class = RightsRestrictionReasonSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('reason',)
    queryset = RightsRestrictionReason.objects.all().order_by('reason')
