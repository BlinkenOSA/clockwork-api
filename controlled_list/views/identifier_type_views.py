from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import IdentifierType
from controlled_list.serializers import IdentifierTypeSerializer, IdentifierTypeSelectSerializer


class IdentifierTypeList(generics.ListCreateAPIView):
    queryset = IdentifierType.objects.all()
    serializer_class = IdentifierTypeSerializer


class IdentifierTypeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = IdentifierType.objects.all()
    serializer_class = IdentifierTypeSerializer


class IdentifierTypeSelectList(generics.ListAPIView):
    serializer_class = IdentifierTypeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('type',)
    queryset = IdentifierType.objects.all().order_by('type')
