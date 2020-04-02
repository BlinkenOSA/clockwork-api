from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import PersonRole
from controlled_list.serializers import PersonRoleSerializer, PersonRoleSelectSerializer


class PersonRoleList(generics.ListCreateAPIView):
    queryset = PersonRole.objects.all()
    serializer_class = PersonRoleSerializer


class PersonRoleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = PersonRole.objects.all()
    serializer_class = PersonRoleSerializer


class PersonRoleSelectList(generics.ListAPIView):
    serializer_class = PersonRoleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('role',)
    queryset = PersonRole.objects.all().order_by('role')
