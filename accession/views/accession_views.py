from datetime import date
from typing import Optional

from django.db.models import QuerySet
from django.db.models.query_utils import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from django_filters import rest_framework as filters
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from accession.models import Accession
from accession.serializers import AccessionSelectSerializer, AccessionListSerializer, \
    AccessionReadSerializer, AccessionWriteSerializer
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin


class AccessionFilterClass(filters.FilterSet):
    """
    FilterSet for filtering accessions in list views.

    Provides three filtering mechanisms:
        - search: Case-insensitive text search across multiple fields.
        - transfer_year: Filters by year extracted from transfer_date.
        - fonds: Filters by archival fonds number (string or numeric).

    Filters are used by AccessionList (ListCreateAPIView).
    """
    search = filters.CharFilter(label='Search', method='filter_search')
    transfer_year = filters.NumberFilter(label='Transfer Year', method='filter_year')
    fonds = filters.CharFilter(label='Fonds', method='filter_fonds')

    def filter_search(self, queryset: QuerySet[Accession], name: str, value: str) -> QuerySet[Accession]:
        """Full-text search across accession title and archival unit fields."""
        return queryset.filter(
            Q(archival_unit__title__icontains=value) |
            Q(archival_unit_legacy_name__icontains=value) |
            Q(title__icontains=value)
        )

    def filter_year(self, queryset: QuerySet[Accession], name: str, value: str) -> QuerySet[Accession]:
        """Filters accessions by transfer year."""
        return queryset.filter(transfer_date__startswith=value)

    def filter_fonds(self, queryset: QuerySet[Accession], name: str, value: str) -> QuerySet[Accession]:
        """
        Filters accessions by fonds number.

        If the value is numeric, matches either:
            - archival_unit.fonds
            - archival_unit_legacy_number

        Otherwise, returns no results.
        """
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
    """
    Lists all accessions or creates a new accession.

    Features:
        - Filtering support via AccessionFilterClass
        - Ordering support based on seq, transfer_date, fonds, legacy fonds number
        - Automatically logs create actions (AuditLogMixin)
        - Selects serializer dynamically based on HTTP method
            GET  -> AccessionListSerializer
            POST -> AccessionWriteSerializer
    """
    queryset = Accession.objects.all()
    filterset_class = AccessionFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    ordering_fields = ['seq', 'transfer_date', 'archival_unit__fonds', 'archival_unit_legacy_number']
    method_serializer_classes = {
        ('GET', ): AccessionListSerializer,
        ('POST', ): AccessionWriteSerializer
    }


class AccessionPreCreate(APIView):
    """
    Provides preliminary data for creating a new accession.

    Returns the next sequential accession number (seq) for the current year.
    Example: 2025/003

    Useful for pre-populating forms before submission.
    """
    def get(self, request: Request, format: Optional[str] = None) -> Response:
        """Returns the next accession sequence number for the current year."""
        year = date.today().year
        sequence = Accession.objects.filter(date_created__year=year).count()
        response = {
            'seq': '%d/%03d' % (year, sequence + 1),
        }
        return Response(response)


class AccessionDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single accession.

    Uses:
        - AccessionReadSerializer for GET
        - AccessionWriteSerializer for PUT/PATCH/DELETE
    Includes full audit logging of modifications.
    """
    queryset = Accession.objects.all()
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): AccessionWriteSerializer
    }


class AccessionSelectList(generics.ListAPIView):
    """
    Lightweight list of accessions for use in select/dropdown fields.

    Returns only:
        - id
        - transfer date
        - seq
        - Archival Unit selection info
        - legacy identifiers
    """
    serializer_class = AccessionSelectSerializer
    queryset = Accession.objects.all().order_by('transfer_date')

