from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from isad.models import Isad
from isad.serializers import IsadSelectSerializer, IsadReadSerializer, IsadWriteSerializer


class IsadList(MethodSerializerMixin, generics.ListCreateAPIView):
    queryset = Isad.objects.all()
    method_serializer_classes = {
        ('GET', ): IsadReadSerializer,
        ('POST', ): IsadWriteSerializer
    }


class IsadDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Isad.objects.all()
    method_serializer_classes = {
        ('GET', ): IsadReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): IsadWriteSerializer
    }


class IsadPublish(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action')
        isad_id = self.kwargs.get('pk')
        isad = get_object_or_404(Isad, pk=isad_id)

        if action == 'publish':
            isad.publish(request.user)
            return Response(status=status.HTTP_200_OK)
        else:
            isad.unpublish()
            return Response(status=status.HTTP_200_OK)


class IsadSelectList(generics.ListAPIView):
    serializer_class = IsadSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter, DjangoFilterBackend)
    filterset_fields = ('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series', 'description_level',)
    search_fields = ('reference_code', 'title')
    queryset = Isad.objects.all().order_by('archival_unit__fonds', 'archival_unit__subfonds', 'archival_unit__series')