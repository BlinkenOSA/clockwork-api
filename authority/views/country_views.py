from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Country
from authority.serializers import CountrySerializer, CountrySelectSerializer


class CountryList(generics.ListCreateAPIView):
    queryset = Country.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['country', 'alpha2', 'alpha3']
    search_fields = ('country', 'alpha2', 'alpha3')
    serializer_class = CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CountrySelectList(generics.ListAPIView):
    serializer_class = CountrySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('country',)
    queryset = Country.objects.all().order_by('country')
