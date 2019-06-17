from rest_framework import generics

from accession.models import Accession
from accession.serializers import AccessionSelectSerializer, AccessionReadSerializer, AccessionWriteSerializer
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin


class AccessionList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Accession.objects.all()
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('POST', ): AccessionWriteSerializer
    }


class AccessionDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Accession.objects.all()
    method_serializer_classes = {
        ('GET', ): AccessionReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): AccessionWriteSerializer
    }


class AccessionSelectList(generics.ListAPIView):
    serializer_class = AccessionSelectSerializer
    queryset = Accession.objects.all().order_by('transfer_date')

