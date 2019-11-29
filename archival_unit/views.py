from rest_framework import generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSelectSerializer, ArchivalUnitReadSerializer, \
    ArchivalUnitWriteSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin


class ArchivalUnitList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = ArchivalUnit.objects.all()
    method_serializer_classes = {
        ('GET', ): ArchivalUnitReadSerializer,
        ('POST', ): ArchivalUnitWriteSerializer
    }


class ArchivalUnitDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ArchivalUnit.objects.all()
    method_serializer_classes = {
        ('GET', ): ArchivalUnitReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ArchivalUnitWriteSerializer
    }


class ArchivalUnitSelectList(generics.ListAPIView):
    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('fonds', 'subfonds', 'series', 'level')
    search_fields = ['title', 'reference_code']
    queryset = ArchivalUnit.objects.all().order_by('fonds', 'subfonds', 'series')
