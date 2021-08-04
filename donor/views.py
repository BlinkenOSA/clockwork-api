from django.db.models import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from donor.models import Donor
from donor.serializers import DonorSelectSerializer, DonorReadSerializer, DonorWriteSerializer
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


class DonorList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Donor.objects.all().order_by('name')
    filterset_class = DonorFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    ordering_fields = ['name']
    method_serializer_classes = {
        ('GET', ): DonorReadSerializer,
        ('POST', ): DonorWriteSerializer
    }


class DonorDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
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
