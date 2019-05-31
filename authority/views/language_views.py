from rest_framework import generics
from rest_framework.filters import SearchFilter

from authority.models import Language
from authority.serializers import LanguageSerializer, LanguageSelectSerializer


class LanguageList(generics.ListCreateAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class LanguageDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer


class LanguageSelectList(generics.ListAPIView):
    serializer_class = LanguageSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('language',)
    queryset = Language.objects.all().order_by('language')
