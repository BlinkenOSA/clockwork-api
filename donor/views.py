from rest_framework import generics
from rest_framework.filters import SearchFilter

from donor.models import Donor
from donor.serializers import DonorSerializer, DonorSelectSerializer


class DonorList(generics.ListCreateAPIView):
    queryset = Donor.objects.all()
    serializer_class = DonorSerializer


class DonorDetail(generics.RetrieveUpdateDestroyAPIView):
    queryset = Donor.objects.all()
    serializer_class = DonorSerializer


class DonorSelectList(generics.ListAPIView):
    serializer_class = DonorSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ['name']
    queryset = Donor.objects.all().order_by('name')
