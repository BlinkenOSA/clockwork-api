from rest_framework import generics
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers import FindingAidsSelectSerializer, \
    FindingAidsEntityReadSerializer, FindingAidsEntityWriteSerializer


class FindingAidsCreate(generics.CreateAPIView):
    serializer_class = FindingAidsEntityWriteSerializer

    def get_serializer_context(self):
        context = super(FindingAidsCreate, self).get_serializer_context
        context['container'] = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        return context


class FindingAidsDetail(MethodSerializerMixin, generics.RetrieveUpdateAPIView):
    queryset = FindingAidsEntity.objects.all()
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsEntityWriteSerializer
    }


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
