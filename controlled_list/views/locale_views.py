from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Locale
from controlled_list.serializers import LocaleSerializer, LocaleSelectSerializer


class LocaleList(generics.ListCreateAPIView):
    queryset = Locale.objects.all()
    serializer_class = LocaleSerializer


class LocaleDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Locale.objects.all()
    serializer_class = LocaleSerializer


class LocaleSelectList(generics.ListAPIView):
    serializer_class = LocaleSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('locale',)
    queryset = Locale.objects.all().order_by('locale')
