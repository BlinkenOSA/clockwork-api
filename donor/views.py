from django.db.models import Q
from rest_framework import generics
from rest_framework.filters import OrderingFilter
from rest_framework.filters import SearchFilter
from rest_framework.permissions import AllowAny

from donor.models import Donor
from donor.serializers import DonorSerializer, DonorSelectSerializer
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


class DonorList(generics.ListCreateAPIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    queryset = Donor.objects.all().order_by('name')
    filter_class = DonorFilterClass
    filter_backends = [OrderingFilter, filters.DjangoFilterBackend]
    ordering_fields = ['name']
    serializer_class = DonorSerializer


class DonorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Donor.objects.all()
    serializer_class = DonorSerializer


class DonorSelectList(generics.ListAPIView):
    serializer_class = DonorSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['name']
    queryset = Donor.objects.all().order_by('name')
