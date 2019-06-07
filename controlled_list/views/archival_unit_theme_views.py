from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ArchivalUnitTheme
from controlled_list.serializers import ArchivalUnitThemeSerializer, ArchivalUnitThemeSelectSerializer


class ArchivalUnitThemeList(generics.ListCreateAPIView):
    queryset = ArchivalUnitTheme.objects.all()
    serializer_class = ArchivalUnitThemeSerializer


class ArchivalUnitThemeDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ArchivalUnitTheme.objects.all()
    serializer_class = ArchivalUnitThemeSerializer


class ArchivalUnitThemeSelectList(generics.ListAPIView):
    serializer_class = ArchivalUnitThemeSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('theme',)
    queryset = ArchivalUnitTheme.objects.all().order_by('theme')
