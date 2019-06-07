from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import LanguageUsage
from controlled_list.serializers import LanguageUsageSerializer, LanguageUsageSelectSerializer


class LanguageUsageList(generics.ListCreateAPIView):
    queryset = LanguageUsage.objects.all()
    serializer_class = LanguageUsageSerializer


class LanguageUsageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = LanguageUsage.objects.all()
    serializer_class = LanguageUsageSerializer


class LanguageUsageSelectList(generics.ListAPIView):
    serializer_class = LanguageUsageSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('usage',)
    queryset = LanguageUsage.objects.all().order_by('usage')
