from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ExtentUnit
from controlled_list.serializers import ExtentUnitSerializer, ExtentUnitSelectSerializer


class ExtentUnitList(generics.ListCreateAPIView):
    queryset = ExtentUnit.objects.all()
    serializer_class = ExtentUnitSerializer


class ExtentUnitDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ExtentUnit.objects.all()
    serializer_class = ExtentUnitSerializer


class ExtentUnitSelectList(generics.ListAPIView):
    serializer_class = ExtentUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('unit',)
    queryset = ExtentUnit.objects.all().order_by('unit')
