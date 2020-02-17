from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Genre
from authority.serializers import GenreSerializer, GenreSelectSerializer


class GenreList(generics.ListCreateAPIView):
    queryset = Genre.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['genre']
    search_fields = ('genre',)
    serializer_class = GenreSerializer


class GenreDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer


class GenreSelectList(generics.ListAPIView):
    serializer_class = GenreSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('genre',)
    queryset = Genre.objects.all().order_by('genre')
