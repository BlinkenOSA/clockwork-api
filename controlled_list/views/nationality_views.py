from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Locale, Nationality
from controlled_list.serializers import LocaleSerializer, LocaleSelectSerializer, NationalitySerializer, \
    NationalitySelectSerializer


class NationalityList(generics.ListCreateAPIView):
    queryset = Locale.objects.all()
    serializer_class = NationalitySerializer


class NationalityDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Locale.objects.all()
    serializer_class = NationalitySerializer


class NationalitySelectList(generics.ListAPIView):
    serializer_class = NationalitySelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('nationality',)
    queryset = Nationality.objects.all().order_by('nationality')
