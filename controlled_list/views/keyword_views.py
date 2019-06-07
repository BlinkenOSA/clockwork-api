from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import Keyword
from controlled_list.serializers import KeywordSerializer, KeywordSelectSerializer


class KeywordList(generics.ListCreateAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class KeywordDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Keyword.objects.all()
    serializer_class = KeywordSerializer


class KeywordSelectList(generics.ListAPIView):
    serializer_class = KeywordSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('keyword',)
    queryset = Keyword.objects.all().order_by('keyword')
