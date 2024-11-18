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
    search = filters.CharFilter(label='Search', method='filter_search')

    def filter_search(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value) |
            Q(email__icontains=value) |
            Q(country__country__icontains=value)
        )

    class Meta:
        model = Donor
        fields = ['search']


class DonorList(AuditLogMixin, MethodSerializerMixin, generics.ListCreateAPIView):
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
    queryset = Donor.objects.all()
    method_serializer_classes = {
        ('GET', ): DonorReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): DonorWriteSerializer
    }


class DonorSelectList(generics.ListAPIView):
    serializer_class = DonorSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['name']
    queryset = Donor.objects.all().order_by('name')
