from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.filters import SearchFilter
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSelectSerializer, ArchivalUnitReadSerializer, \
    ArchivalUnitWriteSerializer, ArchivalUnitFondsSerializer, ArchivalUnitSeriesSerializer, \
    ArchivalUnitPreCreateSerializer
from clockwork_api.mixins.allowed_archival_unit_mixin import ListAllowedArchivalUnitMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from clockwork_api.mixins.read_write_serializer_mixin import ReadWriteSerializerMixin


class ArchivalUnitFilterClass(filters.FilterSet):
    search = filters.CharFilter(label='Search', method='search_filter')

    def search_filter(self, queryset, name, value):
        return ArchivalUnit.objects.filter(
            (
                Q(title__icontains=value) |
                Q(children__title__icontains=value) |
                Q(children__children__title__icontains=value)
            ) & Q(level='F')
        ).distinct()

    class Meta:
        model = ArchivalUnit
        fields = ('fonds',)


class ArchivalUnitPreCreate(generics.RetrieveAPIView):
    queryset = ArchivalUnit.objects.all()
    serializer_class = ArchivalUnitPreCreateSerializer


class ArchivalUnitList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = ArchivalUnit.objects.filter(level='F')
    method_serializer_classes = {
        ('GET', ): ArchivalUnitFondsSerializer,
        ('POST', ): ArchivalUnitWriteSerializer
    }
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ArchivalUnitFilterClass


class ArchivalUnitDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = ArchivalUnit.objects.all()
    method_serializer_classes = {
        ('GET', ): ArchivalUnitReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ArchivalUnitWriteSerializer
    }


class ArchivalUnitSelectList(ListAllowedArchivalUnitMixin, generics.ListAPIView):
    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('fonds', 'subfonds', 'series', 'level', 'parent')
    search_fields = ['title', 'reference_code']
    queryset = ArchivalUnit.objects.all().order_by('fonds', 'subfonds', 'series')


class ArchivalUnitSelectByParentList(generics.ListAPIView):
    serializer_class = ArchivalUnitSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    search_fields = ['title', 'reference_code']

    def get_queryset(self):
        parent_id = self.kwargs.get('parent_id', None)
        user = self.request.user
        if user.user_profile.allowed_archival_units.count() > 0:
            parent_unit = ArchivalUnit.objects.get(pk=parent_id)
            if parent_unit.level == 'F':
                subfonds = ArchivalUnit.objects.filter(parent__id=parent_id)
                queryset = ArchivalUnit.objects.none()
                for archival_unit in user.user_profile.allowed_archival_units.all():
                    queryset |= ArchivalUnit.objects.filter(id=archival_unit.parent.id)
                return queryset & subfonds
            if parent_unit.level == 'SF':
                series = ArchivalUnit.objects.filter(parent__id=parent_id)
                return series & user.user_profile.allowed_archival_units.all()
        else:
            if parent_id:
                return ArchivalUnit.objects.filter(parent_id=parent_id)
            else:
                return ArchivalUnit.objects.none()
