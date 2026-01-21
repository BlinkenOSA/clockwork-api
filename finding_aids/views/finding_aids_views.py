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
    """
    Lists finding aids entities for a given container.

    Intended for container detail pages where users browse folders/items within a
    physical container.

    Queryset behavior:
        - filters by container_id
        - excludes templates
        - orders by folder_no then sequence_no for stable logical ordering
    """

    serializer_class = FindingAidsEntityListSerializer

    def get_queryset(self):
        """
        Returns non-template entities belonging to the container specified in the URL.

        URL kwargs:
            container_id: Container primary key

        Returns:
            QuerySet[FindingAidsEntity]: filtered and ordered, or empty if container_id missing.
        """
        container_id = self.kwargs.get('container_id', None)
        if container_id:
            return FindingAidsEntity.objects.filter(container_id=container_id, is_template=False)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsPreCreate(APIView):
    """
    Provides pre-filled data for creating a new finding aids record.

    This endpoint computes:
        - next folder_no (for L1) or next sequence_no (for L2)
        - the derived archival_reference_code
        - container and archival unit context
        - container-level digitization flags for UI display

    Permissions:
        - restricted via AllowedArchivalUnitPermission
    """

    permission_classes = [AllowedArchivalUnitPermission]

    def get(self, request, *args, **kwargs):
        """
        Builds a default creation payload for a new finding aids entity.

        URL kwargs:
            container_id: Container id used as the parent context

        Query params:
            description_level: 'L1' (folder) or 'L2' (item); default 'L1'
            folder_no: used for L2 creation to indicate the parent folder number; default 0
            level: 'F' or 'I' (domain-level field); default 'F'
            uuid: optional uuid override; generated if missing

        Returns:
            Response[dict]: initial data for the create form.
        """
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
    """
    Creates a new finding aids entity within a given container.

    Behavior:
        - enforces container and archival_unit from the URL container_id
        - records an audit log entry for CREATE

    Permissions:
        - restricted via AllowedArchivalUnitPermission
    """

    serializer_class = FindingAidsEntityWriteSerializer
    permission_classes = [AllowedArchivalUnitPermission]

    def perform_create(self, serializer):
        """
        Persists the record and logs an audit action.

        URL kwargs:
            container_id: Container id used to assign container and archival unit.

        Returns:
            FindingAidsEntity: created instance.
        """
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        instance = serializer.save(container=container, archival_unit=container.archival_unit)
        AuditLogMixin.log_audit_action(user=self.request.user, action='CREATE', instance=instance)
        return instance


class FindingAidsDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a finding aids entity.

    Serializer selection:
        - GET: FindingAidsEntityReadSerializer (full nested representation)
        - PUT/PATCH/DELETE: FindingAidsEntityWriteSerializer (writable nested editor)

    On delete:
        - renumbers sibling entities to keep folder_no/sequence_no contiguous
        - writes an audit log entry for DELETE

    Permissions:
        - restricted via AllowedArchivalUnitPermission
    """

    queryset = FindingAidsEntity.objects.all()
    permission_classes = [AllowedArchivalUnitPermission]
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsEntityWriteSerializer
    }

    def perform_destroy(self, instance):
        """
        Deletes the entity and updates folder/sequence numbering of remaining siblings.

        Renumbering rules are handled by renumber_entries().
        """
        renumber_entries(instance, "delete")
        AuditLogMixin.log_audit_action(user=self.request.user, action='DELETE', instance=instance)
        instance.delete()


class FindingAidsClone(APIView):
    """
    Clones an existing finding aids entity.

    Clone behavior:
        - renumbers affected siblings first (to make room for the clone)
        - creates a deep clone via model_clone (make_clone)
        - prefixes title with "[COPY] "
        - increments folder_no (L1) or sequence_no (L2)
        - resets publication and update metadata fields
        - records an audit log entry for CLONE
    """

    def post(self, request, *args, **kwargs):
        """
        Creates a clone of the specified entity.

        URL kwargs:
            pk: FindingAidsEntity id to clone

        Returns:
            HTTP 200 on success.
        """
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
    """
    Performs a state-changing action on a finding aids entity.

    Supported actions:
        - publish: mark published and set published metadata
        - unpublish: unpublish and clear published metadata
        - set_confidential: mark record as confidential
        - (default): set_non_confidential (any other action value)

    This is a lightweight endpoint for UI buttons/toggles.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the requested action to the target entity.

        URL kwargs:
            action: action string (publish|unpublish|set_confidential|...)
            pk: FindingAidsEntity id

        Returns:
            HTTP 200 on completion.
        """
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
    """
    Returns a non-paginated list of finding aids entities for selection widgets.

    Intended for autocomplete/dropdowns scoped to a container.

    Search:
        - enabled via SearchFilter for basic text matching.
    """

    serializer_class = FindingAidsSelectSerializer
    pagination_class = None
    filter_backends = (SearchFilter,)
    search_fields = ('title', 'description', 'archival_reference_code')

    def get_queryset(self):
        """
        Returns entities in the specified container ordered by folder/sequence.

        URL kwargs:
            container_id: Container id used to scope the selection list.
        """
        container = get_object_or_404(Container, pk=self.kwargs.get('container_id', None))
        qs = FindingAidsEntity.objects.filter(
            is_template=False,
            container=container
        ).order_by('folder_no', 'sequence_no')
        return qs


class FindingAidsGetNextFolder(APIView):
    """
    Computes the next folder/sequence numbers and reference code for creation.

    This is used by clients to quickly fetch the next available identifiers
    without pulling full entity lists.

    Behavior differs by description_level:
        - L1: next folder_no for the container (sequence_no is 0)
        - L2: next sequence_no within a given folder_no (requires folder_no param)
    """

    def get(self, request, *args, **kwargs):
        """
        Returns the next folder_no/sequence_no and derived archival_reference_code.

        URL kwargs:
            container_id: Container id

        Query params:
            description_level: 'L1' or 'L2'; default 'L1'
            folder_no: required for L2 sequencing

        Returns:
            Response[dict]: numbering and reference code values.
        """
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
    """
    Renumbers sibling finding aids entities after delete or before clone.

    Goal:
        Keep folder_no and sequence_no values contiguous and stable after an entity
        is removed or duplicated.

    Actions:
        - "delete": close gaps by decrementing folder_no or sequence_no where appropriate
        - "clone": make room by incrementing sequence_no (or folder_no) for subsequent entities

    Rules:
        - L1 entities:
            - renumber folder_no for subsequent folders only when the deleted folder
              has no remaining L2 items
            - for clone, increment folder_no for subsequent folders
        - L2 entities:
            - if deleting the last item in a folder, potentially renumber subsequent folders
            - otherwise renumber subsequent items in the same folder by decrementing sequence_no
            - for clone, increment sequence_no for subsequent items in the same folder
    """

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
