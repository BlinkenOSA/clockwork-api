from rest_framework import generics
from rest_framework.filters import SearchFilter

from authority.models import Place
from authority.serializers import PlaceSerializer, PlaceSelectSerializer


class PlaceList(generics.ListCreateAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class PlaceDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Place.objects.all()
    serializer_class = PlaceSerializer


class PlaceSelectList(generics.ListAPIView):
    serializer_class = PlaceSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('place',)
    queryset = Place.objects.all().order_by('place')
