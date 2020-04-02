from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import DateType
from controlled_list.serializers import DateTypeSerializer, DateTypeSelectSerializer


class DateTypeList(generics.ListCreateAPIView):
    queryset = DateType.objects.all()
    serializer_class = DateTypeSerializer


class DateTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = DateType.objects.all()
    serializer_class = DateTypeSerializer


class DateTypeSelectList(generics.ListAPIView):
    serializer_class = DateTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = DateType.objects.all().order_by('type')
