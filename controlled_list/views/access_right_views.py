from rest_framework import generics
from rest_framework.filters import SearchFilter

from controlled_list.models import AccessRight
from controlled_list.serializers import AccessRightSerializer, AccessRightSelectSerializer


class AccessRightList(generics.ListCreateAPIView):
    queryset = AccessRight.objects.all()
    serializer_class = AccessRightSerializer


class AccessRightDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = AccessRight.objects.all()
    serializer_class = AccessRightSerializer


class AccessRightSelectList(generics.ListAPIView):
    serializer_class = AccessRightSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('statement',)
    queryset = AccessRight.objects.all().order_by('statement')
