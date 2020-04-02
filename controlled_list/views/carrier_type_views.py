from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import CarrierType
from controlled_list.serializers import CarrierTypeSerializer, CarrierTypeSelectSerializer


class CarrierTypeList(generics.ListCreateAPIView):
    queryset = CarrierType.objects.all()
    serializer_class = CarrierTypeSerializer


class CarrierTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CarrierType.objects.all()
    serializer_class = CarrierTypeSerializer


class CarrierTypeSelectList(generics.ListAPIView):
    serializer_class = CarrierTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = CarrierType.objects.all().order_by('type')
