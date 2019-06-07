from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import RightsRestrictionReason
from controlled_list.serializers import RightsRestrictionReasonSerializer, RightsRestrictionReasonSelectSerializer


class RightsRestrictionReasonList(generics.ListCreateAPIView):
    queryset = RightsRestrictionReason.objects.all()
    serializer_class = RightsRestrictionReasonSerializer


class RightsRestrictionReasonDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = RightsRestrictionReason.objects.all()
    serializer_class = RightsRestrictionReasonSerializer


class RightsRestrictionReasonSelectList(generics.ListAPIView):
    serializer_class = RightsRestrictionReasonSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('reason',)
    queryset = RightsRestrictionReason.objects.all().order_by('reason')
