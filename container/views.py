from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from container.serializers import ContainerReadSerializer, ContainerWriteSerializer, ContainerSelectSerializer


class ContainerList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Container.objects.all()
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('POST', ): ContainerWriteSerializer
    }


class ContainerDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Container.objects.all()
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }


class ContainerSelectList(generics.ListAPIView):
    serializer_class = ContainerSelectSerializer
    queryset = Container.objects.all().order_by('archival_unit__fonds',
                                                'archival_unit__subfonds',
                                                'archival_unit__series',
                                                'container_no')
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ('archival_unit', 'digital_version_exists')


class ContainerDetailByBarcode(MethodSerializerMixin, generics.RetrieveUpdateAPIView):
    queryset = Container.objects.all()
    serializer_class = ContainerReadSerializer
    lookup_field = 'barcode'
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }