from rest_framework import generics
from rest_framework.filters import SearchFilter

from authority.models import Country
from authority.serializers import CountrySerializer


class CountryList(generics.ListCreateAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CountrySelectList(generics.ListAPIView):
    serializer_class = CountrySerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('country',)
    queryset = Country.objects.all().order_by('country')
