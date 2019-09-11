from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import AllowAny
from django_filters import rest_framework as filters

from accession.models import Accession
from accession.serializers import AccessionSelectSerializer, AccessionReadSerializer, AccessionWriteSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin


class AccessionFilterClass(filters.FilterSet):
    search = filters.CharFilter(label='Search', method='filter_search')
    transfer_year = filters.NumberFilter(label='Transfer Year', method='filter_year')
    fonds = filters.CharFilter(label='Fonds', method='filter_fonds')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(archival_unit__title__icontains=value) |
            Q(archival_unit_legacy_name__icontains=value) |
            Q(title__icontains=value)
        )

    def filter_year(self, queryset, name, value):
        return queryset.filter(transfer_date__startswith=value)

    def filter_fonds(self, queryset, name, value):
        if value.isdigit():
            return queryset.filter(
                Q(archival_unit__fonds=value) | Q(archival_unit_legacy_number=value)
            )
        else:
            return Accession.objects.none()

    class Meta:
        model = Accession
        fields = ['search', 'transfer_year', 'fonds']


class AccessionList(MethodSerializerMixin, generics.ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Accession.objects.all()
    filter_class = AccessionFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    ordering_fields = ['seq', 'transfer_date', 'archival_unit__fonds', 'archival_unit_legacy_number']
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('POST', ): AccessionWriteSerializer
    }


class AccessionDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Accession.objects.all()
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): AccessionWriteSerializer
    }


class AccessionSelectList(generics.ListAPIView):
    serializer_class = AccessionSelectSerializer
    queryset = Accession.objects.all().order_by('transfer_date')

