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
    def get(self, *args, **kwargs):
        archival_unit_id = self.kwargs.get('pk', None)
        archival_unit = get_object_or_404(ArchivalUnit, pk=archival_unit_id)
        container = Container.objects.filter(archival_unit=archival_unit).reverse().first()
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
    serializer_class = ContainerWriteSerializer


class ContainerList(generics.ListAPIView):
    serializer_class = ContainerListSerializer

    def get_queryset(self):
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
    queryset = Container.objects.all()
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }

    def perform_destroy(self, instance):
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
    def put(self, request, *args, **kwargs):
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
    def put(self, request, *args, **kwargs):
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
    queryset = Container.objects.all()
    serializer_class = ContainerReadSerializer
    lookup_field = 'barcode'
    method_serializer_classes = {
        ('GET', ): ContainerReadSerializer,
        ('PUT', 'PATCH', 'DELETE'): ContainerWriteSerializer
    }