from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Building
from controlled_list.serializers import BuildingSerializer, BuildingSelectSerializer


class BuildingList(generics.ListCreateAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer


class BuildingDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Building.objects.all()
    serializer_class = BuildingSerializer


class BuildingSelectList(generics.ListAPIView):
    serializer_class = BuildingSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('building',)
    queryset = Building.objects.all().order_by('building')
