from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Corporation
from authority.serializers import CorporationSerializer, CorporationSelectSerializer


class CorporationList(generics.ListCreateAPIView):
    queryset = Corporation.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['name',]
    search_fields = ('name', 'corporationotherformat__name')
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
