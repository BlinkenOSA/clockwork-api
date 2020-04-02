from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import PrimaryType
from controlled_list.serializers import PrimaryTypeSerializer, PrimaryTypeSelectSerializer


class PrimaryTypeList(generics.ListCreateAPIView):
    queryset = PrimaryType.objects.all()
    serializer_class = PrimaryTypeSerializer


class PrimaryTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PrimaryType.objects.all()
    serializer_class = PrimaryTypeSerializer


class PrimaryTypeSelectList(generics.ListAPIView):
    serializer_class = PrimaryTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = PrimaryType.objects.all().order_by('type')
