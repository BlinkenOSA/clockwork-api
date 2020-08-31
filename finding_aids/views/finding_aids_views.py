from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers import FindingAidsSelectSerializer, \
    FindingAidsEntityReadSerializer, FindingAidsEntityWriteSerializer, FindingAidsEntityListSerializer


class FindingAidsList(generics.ListAPIView):
    serializer_class = FindingAidsEntityListSerializer

    def get_queryset(self):
        container_id = self.request.query_params.get('container', None)
        if container_id:
            return FindingAidsEntity.objects.filter(container_id=container_id, is_template=False)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsCreate(generics.CreateAPIView):
    serializer_class = FindingAidsEntityWriteSerializer

    def perform_create(self, serializer):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        serializer.save(container=container, archival_unit=container.archival_unit)


class FindingAidsDetail(MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FindingAidsEntity.objects.all()
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsEntityWriteSerializer
    }

    def perform_destroy(self, instance):
        renumber_entries(instance, -1)
        instance.delete()


class FindingAidsClone(APIView):
    def post(self, request, *args, **kwargs):
        fa_id = self.kwargs.get('pk', None)
        finding_aids = get_object_or_404(FindingAidsEntity, pk=fa_id)

        renumber_entries(finding_aids, 1)

        clone = finding_aids.make_clone()
        clone.title = '[COPY] ' + clone.title
        if finding_aids.description_level == 'L1':
            clone.folder_no += 1
        else:
            clone.sequence_no += 1
        clone.save()
        return Response(status=status.HTTP_200_OK)


class FindingAidsAction(APIView):
    def put(self, request, *args, **kwargs):
        action = self.kwargs.get('action', None)
        fa_id = self.kwargs.get('pk', None)
        finding_aids = get_object_or_404(FindingAidsEntity, pk=fa_id)

        if action == 'publish':
            finding_aids.publish(request.user)
        elif action == 'unpublish':
            finding_aids.unpublish()
        elif action == 'set_confidential':
            finding_aids.set_confidential()
        else:
            finding_aids.set_non_confidential()
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


def renumber_entries(finding_aids, difference):
    if finding_aids.description_level == 'L1':
        fa_records = FindingAidsEntity.objects.filter(
            container=finding_aids.container,
            folder_no__gt=finding_aids.folder_no
        )
        for fa in fa_records.iterator():
            fa.folder_no = fa.folder_no + difference
            fa.save()
    else:
        fa_records = FindingAidsEntity.objects.filter(
            container=finding_aids.container,
            folder_no__gt=finding_aids.folder_no,
            sequence_no__gt=finding_aids.sequence_no
        )
        for fa in fa_records.iterator():
            fa.sequence_no = fa.sequence_no + difference
            fa.save()
