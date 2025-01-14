import uuid

from django.utils import timezone
from rest_framework import generics, status
from rest_framework.filters import SearchFilter
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from clockwork_api.permissons.allowed_archival_unit_permission import AllowedArchivalUnitPermission
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsSelectSerializer, \
    FindingAidsEntityReadSerializer, FindingAidsEntityWriteSerializer, FindingAidsEntityListSerializer


class FindingAidsList(generics.ListAPIView):
    serializer_class = FindingAidsEntityListSerializer

    def get_queryset(self):
        container_id = self.kwargs.get('container_id', None)
        if container_id:
            return FindingAidsEntity.objects.filter(container_id=container_id, is_template=False)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsPreCreate(APIView):
    permission_classes = [AllowedArchivalUnitPermission]

    def get(self, request, *args, **kwargs):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        description_level = self.request.query_params.get('description_level', 'L1')
        folder_no = self.request.query_params.get('folder_no', 0)
        level = self.request.query_params.get('level', 'F')
        guid = self.request.query_params.get('uuid', uuid.uuid4())

        if description_level == 'L1':
            fa_entities = FindingAidsEntity.objects.filter(container=container, level=level)
            folder_no = fa_entities.count() + 1
            sequence_no = 0
            reference_code = "%s:%s/%s" % (container.archival_unit.reference_code, container.container_no, folder_no)
        else:
            fa_entities = FindingAidsEntity.objects.filter(container=container, level=level, folder_no=folder_no)
            sequence_no = fa_entities.count() + 1
            reference_code = "%s:%s/%s-%s" % (
                container.archival_unit.reference_code,
                container.container_no,
                folder_no,
                sequence_no
            )

        if container.digital_version_exists:
            digital_version_exists_container = {
                'digital_version': True,
                'digital_version_online': container.digital_version_online,
                'digital_version_research_cloud': container.digital_version_research_cloud,
                'digital_version_research_cloud_path': container.digital_version_research_cloud_path,
                'digital_version_barcode': container.barcode
            }
        else:
            digital_version_exists_container = {
                'digital_version': False
            }

        data = {
            'archival_unit': container.archival_unit_id,
            'archival_unit_title_full': container.archival_unit.title_full,
            'container': "%s #%s" % (container.carrier_type.type, container.container_no),
            'container_id': container.id,
            'folder_no': folder_no,
            'sequence_no': sequence_no,
            'description_level': description_level,
            'archival_reference_code': reference_code,
            'digital_version_exists_container': digital_version_exists_container,
            'level': level,
            'uuid': guid
        }
        return Response(data)


class FindingAidsCreate(AuditLogMixin, generics.CreateAPIView):
    serializer_class = FindingAidsEntityWriteSerializer
    permission_classes = [AllowedArchivalUnitPermission]

    def perform_create(self, serializer):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        instance = serializer.save(container=container, archival_unit=container.archival_unit)
        AuditLogMixin.log_audit_action(user=self.request.user, action='CREATE', instance=instance)
        return instance


class FindingAidsDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FindingAidsEntity.objects.all()
    permission_classes = [AllowedArchivalUnitPermission]
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsEntityWriteSerializer
    }

    def perform_destroy(self, instance):
        renumber_entries(instance, "delete")
        AuditLogMixin.log_audit_action(user=self.request.user, action='DELETE', instance=instance)
        instance.delete()


class FindingAidsClone(APIView):
    def post(self, request, *args, **kwargs):
        fa_id = self.kwargs.get('pk', None)
        finding_aids = get_object_or_404(FindingAidsEntity, pk=fa_id)

        renumber_entries(finding_aids, "clone")

        clone = finding_aids.make_clone()
        clone.title = '[COPY] ' + clone.title
        if finding_aids.description_level == 'L1':
            clone.folder_no += 1
        else:
            clone.sequence_no += 1
        clone.published = False
        clone.user_created = request.user.username
        clone.date_created = timezone.now()
        clone.user_updated = None
        clone.date_updated = None
        clone.save()

        AuditLogMixin.log_audit_action(user=request.user, action='CLONE', instance=clone)

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


class FindingAidsGetNextFolder(APIView):
    def get(self, request, *args, **kwargs):
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        description_level = self.request.query_params.get('description_level', 'L1')
        folder_no = self.request.query_params.get('folder_no', None)

        if description_level == 'L1':
            fa_entities = FindingAidsEntity.objects.filter(container=container)
            folder_no = fa_entities.count() + 1
            reference_code = "%s:%s/%s" % (container.archival_unit.reference_code, container.container_no, folder_no)
            return Response({
                'folder_no': folder_no,
                'sequence_no': 0,
                'archival_reference_code': reference_code
            })
        else:
            fa_entities = FindingAidsEntity.objects.filter(
                container=container,
                description_level='L2',
                folder_no=folder_no)
            sequence_no = fa_entities.count() + 1
            reference_code = "%s:%s/%s-%s" % (container.archival_unit.reference_code, container.container_no, folder_no, sequence_no)
            return Response({
                'folder_no': folder_no,
                'sequence_no': sequence_no,
                'archival_reference_code': reference_code
            })


def renumber_entries(finding_aids, action):
    # L1 entities
    if finding_aids.description_level == 'L1':
        folders = FindingAidsEntity.objects.filter(container=finding_aids.container,
                                                   folder_no__gt=finding_aids.folder_no)

        # Delete L1 entities
        if action == 'delete':
            item_count = FindingAidsEntity.objects.filter(container=finding_aids.container,
                                                          description_level='L2',
                                                          folder_no=finding_aids.folder_no).count()
            if item_count == 0:
                for folder in folders:
                    folder.folder_no -= 1
                    folder.save()

        # Clone L1 entities
        else:
            for folder in folders:
                folder.folder_no += 1
                folder.save()

    # L2 entities
    else:
        folders = FindingAidsEntity.objects.filter(container=finding_aids.container,
                                                   folder_no__gt=finding_aids.folder_no)
        items = FindingAidsEntity.objects.filter(container=finding_aids.container,
                                                 level=finding_aids.level,
                                                 folder_no=finding_aids.folder_no,
                                                 sequence_no__gt=finding_aids.sequence_no)

        # Delete entities
        if action == 'delete':
            item_count = FindingAidsEntity.objects.filter(container=finding_aids.container,
                                                          description_level='L2',
                                                          folder_no=finding_aids.folder_no).count()
            if item_count == 0:
                for folder in folders:
                    folder.folder_no -= 1
                    folder.save()
            else:
                for item in items:
                    item.sequence_no -= 1
                    item.save()
        # Clone entities
        else:
            for item in items:
                item.sequence_no += 1
                item.save()
