from django.conf import settings
from django.db import transaction
from django.db.models import Count, IntegerField, OuterRef, Subquery, Value, F
from django.db.models.functions import Coalesce
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from accounts.permissions import (
    accessible_unprocessed_series,
    can_access_unprocessed_series,
    is_unprocessed_series,
)
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from container.serializers import ContainerReadSerializer, ContainerWriteSerializer, \
    ContainerListSerializer, ContainerMoveSerializer
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity


class UnprocessedContainerAccessMixin:
    """Restrict containers in the holding fonds to the dedicated allowlist."""

    def get_queryset(self):
        queryset = super().get_queryset()
        accessible_series = accessible_unprocessed_series(self.request.user)
        return queryset.exclude(
            archival_unit__fonds=settings.UNPROCESSED_MATERIALS_FONDS
        ) | queryset.filter(archival_unit__in=accessible_series)

    def perform_update(self, serializer):
        archival_unit = serializer.validated_data.get(
            'archival_unit',
            serializer.instance.archival_unit,
        )
        if is_unprocessed_series(archival_unit) and not can_access_unprocessed_series(
                self.request.user, archival_unit):
            raise PermissionDenied('You are not allowed to access this unprocessed series.')
        super().perform_update(serializer)


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
        if is_unprocessed_series(archival_unit) and not can_access_unprocessed_series(
                self.request.user, archival_unit):
            raise PermissionDenied('You are not allowed to access this unprocessed series.')
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

    def perform_create(self, serializer):
        archival_unit = serializer.validated_data['archival_unit']
        if is_unprocessed_series(archival_unit) and not can_access_unprocessed_series(
                self.request.user, archival_unit):
            raise PermissionDenied('You are not allowed to access this unprocessed series.')
        super().perform_create(serializer)


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
            total_number_count = FindingAidsEntity.objects.filter(
                container=OuterRef('pk'),
                is_template=False
            ).values('container').annotate(total=Count('id')).values('total')[:1]
            total_published_number_count = FindingAidsEntity.objects.filter(
                container=OuterRef('pk'),
                is_template=False,
                published=True
            ).values('container').annotate(total=Count('id')).values('total')[:1]
            digital_versions_masters_count = DigitalVersion.objects.filter(
                container=OuterRef('pk'),
                finding_aids_entity__isnull=True,
                level='M'
            ).values('container').annotate(total=Count('id')).values('total')[:1]
            digital_versions_access_copies_count = DigitalVersion.objects.filter(
                container=OuterRef('pk'),
                finding_aids_entity__isnull=True,
                level='A'
            ).values('container').annotate(total=Count('id')).values('total')[:1]
            digital_versions_in_finding_aids_count = DigitalVersion.objects.filter(
                finding_aids_entity__container=OuterRef('pk')
            ).values('finding_aids_entity__container').annotate(total=Count('id')).values('total')[:1]

            def annotate_counts(queryset):
                return queryset.select_related('archival_unit', 'carrier_type').annotate(
                    total_number_count=Coalesce(
                        Subquery(total_number_count, output_field=IntegerField()),
                        Value(0)
                    ),
                    total_published_number_count=Coalesce(
                        Subquery(total_published_number_count, output_field=IntegerField()),
                        Value(0)
                    ),
                    digital_versions_masters_count=Coalesce(
                        Subquery(digital_versions_masters_count, output_field=IntegerField()),
                        Value(0)
                    ),
                    digital_versions_access_copies_count=Coalesce(
                        Subquery(digital_versions_access_copies_count, output_field=IntegerField()),
                        Value(0)
                    ),
                    digital_versions_in_finding_aids_count=Coalesce(
                        Subquery(digital_versions_in_finding_aids_count, output_field=IntegerField()),
                        Value(0)
                    ),
                )

            user = self.request.user
            requested_archival_unit = ArchivalUnit.objects.filter(id=archival_unit_id).first()
            if is_unprocessed_series(requested_archival_unit):
                if can_access_unprocessed_series(user, requested_archival_unit):
                    return annotate_counts(Container.objects.filter(archival_unit_id=archival_unit_id))
                return Container.objects.none()
            if user.user_profile.allowed_archival_units.count() > 0:
                if user.user_profile.allowed_archival_units.filter(id=archival_unit_id).exists():
                    return annotate_counts(Container.objects.filter(archival_unit_id=archival_unit_id))
                return Container.objects.none()
            else:
                return annotate_counts(Container.objects.filter(archival_unit_id=archival_unit_id))
        else:
            return Container.objects.none()


class ContainerDetail(UnprocessedContainerAccessMixin, AuditLogMixin, MethodSerializerMixin,
                      generics.RetrieveUpdateDestroyAPIView):
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
        containers.update(container_no=F('container_no') - 1)


class ContainerMove(APIView):
    """Move a container to the end of another series and compact its source."""

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = ContainerMoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        container_id = serializer.validated_data['container'].id
        source_series = serializer.validated_data['source_series']
        destination_series = serializer.validated_data['destination_series']

        for series in (source_series, destination_series):
            if is_unprocessed_series(series) and not can_access_unprocessed_series(request.user, series):
                raise PermissionDenied('You are not allowed to access this unprocessed series.')

        allowed_archival_units = request.user.user_profile.allowed_archival_units
        if (not request.user.is_superuser and allowed_archival_units.exists() and
                not allowed_archival_units.filter(pk=destination_series.pk).exists()):
            raise PermissionDenied('You are not allowed to access the destination series.')

        # Lock the series rows first so concurrent move operations acquire
        # locks in a predictable order.
        list(ArchivalUnit.objects.select_for_update().filter(
            id__in=sorted((source_series.id, destination_series.id))
        ).order_by('id'))

        source_containers = list(
            Container.objects.select_for_update().filter(
                archival_unit_id=source_series.id
            ).order_by('container_no', 'id')
        )
        destination_containers = list(
            Container.objects.select_for_update().filter(
                archival_unit_id=destination_series.id
            ).order_by('container_no', 'id')
        )

        moved_container = next(
            (item for item in source_containers if item.id == container_id),
            None
        )
        if moved_container is None:
            raise ValidationError({'container': 'The container does not belong to the source series.'})

        source_remaining = [
            item for item in source_containers if item.id != moved_container.id
        ]
        destination_container_no = max(
            (item.container_no for item in destination_containers),
            default=0
        ) + 1

        # Move every source row to a unique temporary number first. This
        # prevents intermediate collisions with the (series, container_no)
        # uniqueness constraint while final numbers are assigned.
        highest_number = max(
            (item.container_no for item in source_containers),
            default=0
        )
        temporary_base = highest_number + len(source_containers) + 1
        for offset, item in enumerate(source_containers):
            Container.objects.filter(pk=item.id).update(
                container_no=temporary_base + offset
            )

        for container_no, item in enumerate(source_remaining, start=1):
            Container.objects.filter(pk=item.id).update(container_no=container_no)

        Container.objects.filter(pk=moved_container.id).update(
            archival_unit_id=destination_series.id,
            container_no=destination_container_no,
            user_updated=request.user.username,
            date_updated=timezone.now(),
        )

        # Finding-aid records duplicate their series and reference code, so
        # refresh them after all affected container numbers have settled.
        affected_ids = [item.id for item in source_containers]
        finding_aids_entities = FindingAidsEntity.objects.select_for_update().select_related(
            'container__archival_unit'
        ).filter(container_id__in=affected_ids)
        for entity in finding_aids_entities:
            entity.archival_unit = entity.container.archival_unit
            entity.user_updated = request.user.username
            entity.date_updated = timezone.now()
            entity.save()

        moved_container.refresh_from_db()
        AuditLogMixin.log_audit_action(
            user=request.user,
            action='UPDATE',
            instance=moved_container,
            changed_fields=['archival_unit', 'container_no'],
        )
        return Response(
            ContainerReadSerializer(moved_container).data,
            status=status.HTTP_200_OK
        )


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
        if action == 'publish':
            for finding_aids_entity in finding_aids_entities:
                finding_aids_entity.publish(request.user)
        else:
            for finding_aids_entity in finding_aids_entities:
                finding_aids_entity.unpublish()
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
        if action == 'publish':
            for finding_aids_entity in finding_aids_entities:
                finding_aids_entity.publish(request.user)
        else:
            for finding_aids_entity in finding_aids_entities:
                finding_aids_entity.unpublish()
        return Response(status=status.HTTP_200_OK)


class ContainerDetailByBarcode(UnprocessedContainerAccessMixin, AuditLogMixin, MethodSerializerMixin,
                               generics.RetrieveUpdateAPIView):
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
