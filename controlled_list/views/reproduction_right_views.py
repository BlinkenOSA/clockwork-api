from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import ReproductionRight
from controlled_list.serializers import ReproductionRightSerializer, ReproductionRightSelectSerializer


class ReproductionRightList(generics.ListCreateAPIView):
    queryset = ReproductionRight.objects.all()
    serializer_class = ReproductionRightSerializer


class ReproductionRightDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = ReproductionRight.objects.all()
    serializer_class = ReproductionRightSerializer


class ReproductionRightSelectList(generics.ListAPIView):
    serializer_class = ReproductionRightSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('statement',)
    queryset = ReproductionRight.objects.all().order_by('statement')
