from datetime import date

from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from django_filters import rest_framework as filters
from rest_framework.response import Response
from rest_framework.views import APIView

from accession.models import Accession
from accession.serializers import AccessionSelectSerializer, AccessionListSerializer, \
    AccessionReadSerializer, AccessionWriteSerializer
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
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


class AccessionList(AuditLogMixin, MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Accession.objects.all()
    filterset_class = AccessionFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    ordering_fields = ['seq', 'transfer_date', 'archival_unit__fonds', 'archival_unit_legacy_number']
    method_serializer_classes = {
        ('GET', ): AccessionListSerializer,
        ('POST', ): AccessionWriteSerializer
    }


class AccessionPreCreate(APIView):
    def get(self, request, format=None):
        year = date.today().year
        sequence = Accession.objects.filter(date_created__year=year).count()
        response = {
            'seq': '%d/%03d' % (year, sequence + 1),
        }
        return Response(response)


class AccessionDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Accession.objects.all()
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): AccessionWriteSerializer
    }


class AccessionSelectList(generics.ListAPIView):
    serializer_class = AccessionSelectSerializer
    queryset = Accession.objects.all().order_by('transfer_date')

