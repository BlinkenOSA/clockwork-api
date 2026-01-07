from rest_framework import generics, status
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from container.serializers import ContainerReadSerializer, ContainerWriteSerializer, ContainerSelectSerializer, \
    ContainerListSerializer
from finding_aids.models import FindingAidsEntity


class ContainerPreCreate(APIView):
    """
    Provides derived defaults required for container creation.

    This endpoint returns the next sequential container number for an
    archival unit, allowing clients to prefill UI forms consistently with
    server-side numbering rules.
    """

    def get(self, *args, **kwargs):
        """
        Returns the archival unit id and the next container number.

        The next container number is computed as:
            - max(container_no) + 1 within the archival unit, or
            - 1 if the archival unit has no containers
        """
        archival_unit_id = self.kwargs.get('pk', None)
        archival_unit = get_object_or_404(ArchivalUnit, pk=archival_unit_id)
        container = Container.objects.filter(archival_unit=archival_unit).order_by('container_no').reverse().first()
        if container:
            response = {
                'archival_unit': archival_unit_id,
                'container_no': container.container_no + 1
            }
        else:
            response = {
                'archival_unit': archival_unit_id,
                'container_no': 1
            }
        return Response(response)


class ContainerCreate(AuditLogMixin, generics.CreateAPIView):
    """
    Creates a new container.

    Uses the write serializer to enforce server-managed fields and applies
    audit logging via AuditLogMixin.
    """

    serializer_class = ContainerWriteSerializer


class ContainerList(generics.ListAPIView):
    """
    Lists containers for an archival series with access filtering.

    If the requesting user has an explicit allowed_archival_units list:
        - Only containers from the requested series are returned when the
          series is included in the user's allowed list.
        - Otherwise an empty queryset is returned.

    If the user has no allowed_archival_units configured:
        - Containers for the requested series are returned without further
          filtering.
    """

    serializer_class = ContainerListSerializer

    def get_queryset(self):
        """
        Returns the queryset for the requested series id.

        The series id is provided via the `series_id` URL parameter and is
        interpreted as an archival unit id.
        """
        archival_unit_id = self.kwargs.get('series_id', None)
        if archival_unit_id:
            user = self.request.user
            if user.user_profile.allowed_archival_units.count() > 0:
                if user.user_profile.allowed_archival_units.filter(id=archival_unit_id).count() > 0:
                    allowed_archival_unit = user.user_profile.allowed_archival_units.get(id=archival_unit_id)
                    return Container.objects.filter(archival_unit_id=allowed_archival_unit.id)
                else:
                    return Container.objects.none()
            else:
                return Container.objects.filter(archival_unit_id=archival_unit_id)
        else:
            return Container.objects.none()


class ContainerDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a container by primary key.

    Serializer behavior:
        - GET uses the read serializer
        - PUT/PATCH/DELETE use the write serializer

    Deletion behavior:
        - After deleting a container, subsequent container numbers within
          the same archival unit are decremented to preserve sequential
          numbering.
        - The delete action is recorded via audit logging.
    """
    queryset = Container.objects.all()
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }

    def perform_destroy(self, instance):
        """
        Deletes the container and re-sequences remaining container numbers.

        After removal, containers with a higher container_no in the same
        archival unit are shifted down by 1 to maintain continuity.
        """
        archival_unit = instance.archival_unit
        containers = Container.objects.filter(
            archival_unit=archival_unit,
            container_no__gt=instance.container_no).order_by('container_no')
        AuditLogMixin.log_audit_action(user=self.request.user, action='DELETE', instance=instance)
        instance.delete()
        for container in containers.iterator():
            container.container_no -= 1
            container.save()


class ContainerPublishAll(APIView):
    """
    Publishes or unpublishes all finding-aid entities for an archival series.

    The action is provided via the `action` URL parameter and is expected
    to be either 'publish' or 'unpublish'.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the requested publish action to all finding-aid entities in a series.

        Publishing is performed by calling FindingAidsEntity.publish(user).
        Unpublishing is performed by calling FindingAidsEntity.unpublish().
        """
        action = self.kwargs.get('action', None)
        archival_unit_id = self.kwargs.get('series', None)

        finding_aids_entities = FindingAidsEntity.objects.filter(archival_unit_id=archival_unit_id)
        for finding_aids in finding_aids_entities.iterator():
            if action == 'publish':
                finding_aids.publish(request.user)
            else:
                finding_aids.unpublish()
        return Response(status=status.HTTP_200_OK)


class ContainerPublish(APIView):
    """
    Publishes or unpublishes all finding-aid entities within a container.

    The action is provided via the `action` URL parameter and is expected
    to be either 'publish' or 'unpublish'.
    """

    def put(self, request, *args, **kwargs):
        """
        Applies the requested publish action to all finding-aid entities in a container.

        Publishing is performed by calling FindingAidsEntity.publish(user).
        Unpublishing is performed by calling FindingAidsEntity.unpublish().
        """
        action = self.kwargs.get('action', None)
        container_id = self.kwargs.get('pk', None)
        container = get_object_or_404(Container, pk=container_id)

        finding_aids_entities = FindingAidsEntity.objects.filter(container=container)
        for finding_aids in finding_aids_entities.iterator():
            if action == 'publish':
                finding_aids.publish(request.user)
            else:
                finding_aids.unpublish()
        return Response(status=status.HTTP_200_OK)


class ContainerDetailByBarcode(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateAPIView):
    """
    Retrieves or updates a container by barcode.

    This view supports barcode-based lookup for workflows that operate on
    physical identifiers rather than internal primary keys.

    Serializer behavior:
        - GET uses the read serializer
        - PUT/PATCH use the write serializer
    """

    queryset = Container.objects.all()
    serializer_class = ContainerReadSerializer
    lookup_field = 'barcode'
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }