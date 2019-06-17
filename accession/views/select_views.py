from rest_framework import generics

from accession.models import AccessionMethod, AccessionCopyrightStatus
from accession.serializers import AccessionMethodSelectSerializer, AccessionCopyrightStatusSelectSerializer


class AccessionMethodSelectList(generics.ListAPIView):
    serializer_class = AccessionMethodSelectSerializer
    queryset = AccessionMethod.objects.all().order_by('method')


class AccessionCopyrightStatusSelectList(generics.ListAPIView):
    serializer_class = AccessionCopyrightStatusSelectSerializer
    queryset = AccessionCopyrightStatus.objects.all().order_by('status')
