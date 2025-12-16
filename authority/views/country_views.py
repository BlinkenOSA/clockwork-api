from rest_framework import generics
from rest_framework.filters import SearchFilter, OrderingFilter

from authority.models import Country
from authority.serializers import CountrySerializer, CountrySelectSerializer


class CountryList(generics.ListCreateAPIView):
    """
    Lists all country authority records or creates a new one.

    GET:
        - Returns a searchable and orderable list of countries.
        - Supports searching by:
            * country name
            * ISO alpha-2 code
            * ISO alpha-3 code

    POST:
        - Creates a new country authority record.
    """

    queryset = Country.objects.all()
    filter_backends = (OrderingFilter, SearchFilter)
    ordering_fields = ['country', 'alpha2', 'alpha3']
    search_fields = ('country', 'alpha2', 'alpha3')
    serializer_class = CountrySerializer


class CountryDetail(generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single country authority record.

    GET:
        - Returns full country details.

    PUT / PATCH:
        - Updates the country record.

    DELETE:
        - Deletes the country record if it is not referenced elsewhere.
    """

    queryset = Country.objects.all()
    serializer_class = CountrySerializer


class CountrySelectList(generics.ListAPIView):
    """
    Returns a lightweight, unpaginated list of countries for selection UIs.

    Features:
        - Alphabetical ordering
        - Searchable by country name
        - Optimized for dropdowns and autocomplete components
    """

    serializer_class = CountrySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('country',)
    queryset = Country.objects.all().order_by('country')
