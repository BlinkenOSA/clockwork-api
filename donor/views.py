from django.db.models import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter

from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from donor.models import Donor
from donor.serializers import DonorSelectSerializer, DonorReadSerializer, DonorWriteSerializer, DonorListSerializer
from django_filters import rest_framework as filters


class DonorFilterClass(filters.FilterSet):
    """
    Filter set for donor list views.

    Provides a single free-text `search` parameter that matches against:
        - donor name
        - email address
        - country name
    """

    search = filters.CharFilter(label='Search', method='filter_search')

    def filter_search(self, queryset, name, value):
        """
        Applies a case-insensitive search across donor identity fields.

        Search targets:
            - name
            - email
            - country.country (display name)
        """
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(country__country__icontains=value)
        )

    class Meta:
        model = Donor
        fields = ['search']


class DonorList(AuditLogMixin, MethodSerializerMixin, generics.ListCreateAPIView):
    """
    Lists and creates donors.

    Serializer behavior:
        - GET returns a compact list representation (DonorListSerializer)
        - POST uses the write serializer (DonorWriteSerializer) to enforce
          donor identity validation and user metadata

    Filtering and ordering:
        - Supports DjangoFilterBackend for:
            - city
            - country
            - search (custom filter)
        - Supports OrderingFilter for:
            - name
            - city
            - country__country
    """

    queryset = Donor.objects.all().order_by('name')
    filterset_class = DonorFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    filterset_fields = ['city', 'country']
    ordering_fields = ['name', 'city', 'country__country']
    method_serializer_classes = {
        ('GET', ): DonorListSerializer,
        ('POST', ): DonorWriteSerializer
    }


class DonorDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a donor.

    Serializer behavior:
        - GET uses the read serializer (DonorReadSerializer)
        - PUT/PATCH/DELETE use the write serializer (DonorWriteSerializer)

    Audit logging is applied via AuditLogMixin.
    """

    queryset = Donor.objects.all()
    method_serializer_classes = {
        ('GET', ): DonorReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): DonorWriteSerializer
    }


class DonorSelectList(generics.ListAPIView):
    """
    Provides a lightweight list of donors for selection widgets.

    This endpoint is intended for dropdowns and autocomplete components:
        - Returns a minimal representation (id + name)
        - Disables pagination
        - Supports search over: name
        - Returns results ordered by name
    """

    serializer_class = DonorSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['name']
    queryset = Donor.objects.all().order_by('name')
