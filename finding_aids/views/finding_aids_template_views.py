import uuid
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer
from finding_aids.serializers.finding_aids_template_serializers import FindingAidsTemplateListSerializer, \
    FindingAidsTemplateWriteSerializer


class FindingAidsTemplateList(generics.ListAPIView):
    """
    Lists finding aids templates for a given series (archival unit).

    Templates are FindingAidsEntity records with `is_template=True`. They act as
    reusable metadata blueprints for creating new finding aids records.

    Queryset behavior:
        - filters by archival_unit_id (series_id)
        - includes only templates
        - orders by folder_no and sequence_no for predictable display
    """

    serializer_class = FindingAidsTemplateListSerializer

    def get_queryset(self):
        """
        Lists finding aids templates for a given series (archival unit).

        Templates are FindingAidsEntity records with `is_template=True`. They act as
        reusable metadata blueprints for creating new finding aids records.

        Queryset behavior:
            - filters by archival_unit_id (series_id)
            - includes only templates
            - orders by folder_no and sequence_no for predictable display
        """
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=True)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsTemplateSelect(generics.ListAPIView):
    """
    Lists finding aids templates for use in selection/lookup widgets.

    This endpoint returns the same dataset as FindingAidsTemplateList but
    disables pagination for UI components that need the full list.
    """

    serializer_class = FindingAidsTemplateListSerializer
    pagination_class = None

    def get_queryset(self):
        """
        Returns templates for the series specified in the URL.

        URL kwargs:
            series_id: ArchivalUnit id (series)

        Returns:
            QuerySet[FindingAidsEntity]: template records, or empty if series_id missing.
        """
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=True)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsTemplatePreCreate(APIView):
    """
    Provides pre-filled data for creating a new finding aids template.

    This is a convenience endpoint for frontends so they can initialize a
    "create template" form with:
        - archival unit context
        - a TEMPLATE reference code
        - default description/level values
        - a UUID
    """

    def get(self, request, *args, **kwargs):
        """
        Builds and returns a default template payload.

        URL kwargs:
            series_id: ArchivalUnit id (series)
            uuid: optional UUID override; generated if missing

        Returns:
            Response[dict]: initial template data for client-side form initialization.
        """
        archival_unit = get_object_or_404(ArchivalUnit, pk=self.kwargs.get('series_id', None))
        guid = self.kwargs.get('uuid', uuid.uuid4())

        reference_code = "%s-TEMPLATE" % archival_unit.reference_code

        data = {
            'archival_unit': archival_unit.id,
            'archival_unit_title_full': archival_unit.title_full,
            'description_level': 'L1',
            'level': 'F',
            'archival_reference_code': reference_code,
            'is_template': True,
            'uuid': guid
        }
        return Response(data)


class FindingAidsTemplateCreate(AuditLogMixin, generics.CreateAPIView):
    """
    Creates a new finding aids template in the given series.

    Uses FindingAidsTemplateWriteSerializer and records an audit log entry
    for the CREATE action.
    """

    serializer_class = FindingAidsTemplateWriteSerializer

    def perform_create(self, serializer):
        """
        Persists the template and writes an audit log entry.

        The archival_unit is enforced from the URL (series_id) regardless of
        client input.

        Returns:
            FindingAidsEntity: created template instance.
        """
        archival_unit = get_object_or_404(ArchivalUnit, pk=self.kwargs.get('series_id', None))
        instance = serializer.save(archival_unit=archival_unit)
        AuditLogMixin.log_audit_action(user=self.request.user, action='CREATE', instance=instance)
        return instance


class FindingAidsTemplateDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    """
    Retrieves, updates, or deletes a single finding aids template.

    Serializer selection:
        - GET: FindingAidsEntityReadSerializer (full read view with nested data)
        - PUT/PATCH/DELETE: FindingAidsTemplateWriteSerializer (writable nested template editor)

    Queryset is restricted to templates only (is_template=True).
    """

    queryset = FindingAidsEntity.objects.filter(is_template=True)
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsTemplateWriteSerializer
    }
