from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import GeoRole
from controlled_list.serializers import GeoRoleSerializer, GeoRoleSelectSerializer


class GeoRoleList(generics.ListCreateAPIView):
    queryset = GeoRole.objects.all()
    serializer_class = GeoRoleSerializer


class GeoRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = GeoRole.objects.all()
    serializer_class = GeoRoleSerializer


class GeoRoleSelectList(generics.ListAPIView):
    serializer_class = GeoRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = GeoRole.objects.all().order_by('role')
