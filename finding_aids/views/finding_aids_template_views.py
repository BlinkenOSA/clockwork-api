import uuid
from rest_framework import generics
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from clockwork_api.mixins.method_serializer_mixin import MethodSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer, \
    FindingAidsEntityWriteSerializer
from finding_aids.serializers.finding_aids_template_serializers import FindingAidsTemplateListSerializer, \
    FindingAidsTemplateWriteSerializer


class FindingAidsTemplateList(generics.ListAPIView):
    serializer_class = FindingAidsTemplateListSerializer

    def get_queryset(self):
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=True)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsTemplateSelect(generics.ListAPIView):
    serializer_class = FindingAidsTemplateListSerializer
    pagination_class = None

    def get_queryset(self):
        series_id = self.kwargs.get('series_id', None)
        if series_id:
            return FindingAidsEntity.objects.filter(archival_unit_id=series_id, is_template=True)\
                .order_by('folder_no', 'sequence_no')
        else:
            return FindingAidsEntity.objects.none()


class FindingAidsTemplatePreCreate(APIView):
    def get(self, request, *args, **kwargs):
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
    serializer_class = FindingAidsTemplateWriteSerializer

    def perform_create(self, serializer):
        archival_unit = get_object_or_404(ArchivalUnit, pk=self.kwargs.get('series_id', None))
        instance = serializer.save(archival_unit=archival_unit)
        AuditLogMixin.log_audit_action(user=self.request.user, action='CREATE', instance=instance)
        return instance


class FindingAidsTemplateDetail(AuditLogMixin, MethodSerializerMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = FindingAidsEntity.objects.filter(is_template=True)
    method_serializer_classes = {
        ('GET', ): FindingAidsEntityReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): FindingAidsTemplateWriteSerializer
    }
