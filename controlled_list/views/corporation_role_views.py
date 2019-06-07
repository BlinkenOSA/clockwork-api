from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import CorporationRole
from controlled_list.serializers import CorporationRoleSerializer, CorporationRoleSelectSerializer


class CorporationRoleList(generics.ListCreateAPIView):
    queryset = CorporationRole.objects.all()
    serializer_class = CorporationRoleSerializer


class CorporationRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = CorporationRole.objects.all()
    serializer_class = CorporationRoleSerializer


class CorporationRoleSelectList(generics.ListAPIView):
    serializer_class = CorporationRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = CorporationRole.objects.all().order_by('role')
