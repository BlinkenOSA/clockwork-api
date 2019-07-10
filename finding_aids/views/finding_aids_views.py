from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers import FindingAidsSelectSerializer, \
    FindingAidsEntityReadSerializer, FindingAidsEntityWriteSerializer


class FindingAidsCreate(generics.CreateAPIView):
    serializer_class = FindingAidsEntityWriteSerializer

    def perform_create(self, serializer):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        serializer.save(container=container, archival_unit=container.archival_unit)


class FindingAidsDetail(MethodSerializerMixin, generics.RetrieveUpdateAPIView):
    queryset = FindingAidsEntity.objects.all()
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsEntityWriteSerializer
    }


class FindingAidsPublish(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action', None)
        fa_id = self.kwargs.get('pk', None)
        finding_aids = get_object_or_404(FindingAidsEntity, pk=fa_id)

        if action == 'publish':
            finding_aids.publish(request.user)
            return Response(status=status.HTTP_200_OK)
        else:
            finding_aids.unpublish()
            return Response(status=status.HTTP_200_OK)


class FindingAidsSelectList(generics.ListAPIView):
    serializer_class = FindingAidsSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('title', 'description', 'archival_reference_code')

    def get_queryset(self):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        qs = FindingAidsEntity.objects.filter(
            is_template=False,
            container=container
        ).order_by('folder_no', 'sequence_no')
        return qs
