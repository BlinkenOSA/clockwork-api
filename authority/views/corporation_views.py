from rest_framework import generics
from rest_framework.filters import SearchFilter

from authority.models import Corporation
from authority.serializers import CorporationSerializer, CorporationSelectSerializer


class CorporationList(generics.ListCreateAPIView):
    queryset = Corporation.objects.all()
    serializer_class = CorporationSerializer


class CorporationDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Corporation.objects.all()
    serializer_class = CorporationSerializer


class CorporationSelectList(generics.ListAPIView):
    serializer_class = CorporationSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('name',)
    queryset = Corporation.objects.all().order_by('name')
