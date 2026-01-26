import re

from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import NotFound
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView, get_object_or_404, RetrieveAPIView

from clockwork_api.authentication import BearerAuthentication
from clockwork_api.mixins.audit_log_mixin import AuditLogMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer
from workflow.permission import APIGroupPermission
from workflow.serializers.container_serializers import ContainerDigitizedSerializer


class GetSetDigitizedContainer(AuditLogMixin, RetrieveUpdateAPIView):
    """
    Retrieves or updates digitization metadata for a container (by barcode).

    This endpoint is designed for long-term preservation workflow scripts.

    Lookup:
        - Uses ``barcode`` as the lookup field.

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission

    Side effects on update:
        - After updating the container, all related finding aids entities
          pointing to the container are saved to trigger their own save logic
          (e.g. derived fields, signals, or downstream synchronization).
    """

    swagger_schema = None
    queryset = Container.objects.all()
    serializer_class = ContainerDigitizedSerializer
    lookup_field = 'barcode'
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    def perform_update(self, serializer):
        """
        Persists the container update and refreshes related finding aids entities.

        Args:
            serializer: The bound serializer instance.

        Notes:
            This intentionally re-saves all FindingAidsEntity records referencing
            the updated container to keep dependent/derived state consistent.
        """
        instance = serializer.save()
        for fa_entity in FindingAidsEntity.objects.filter(container=instance).all():
            fa_entity.save()


class GetContainerMetadata(ListAPIView):
    """
    Returns finding aids metadata for a container (by barcode).

    This endpoint resolves a container by barcode and returns all non-template
    :class:`finding_aids.models.FindingAidsEntity` records attached to it.

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission
    """

    swagger_schema = None
    serializer_class = FindingAidsEntityReadSerializer
    lookup_field = 'barcode'
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    def get_queryset(self):
        """
        Resolves the container and returns its finding aids entities.

        Returns:
            QuerySet[FindingAidsEntity] or None: Non-template finding aids entities
            for the resolved container. If the barcode is unknown, returns None
            and results in an empty response.
        """
        container = Container.objects.filter(barcode=self.kwargs['barcode']).first()
        if container:
            finding_aids = FindingAidsEntity.objects.filter(container=container, is_template=False)
            return finding_aids


class GetContainerMetadataByLegacyID(RetrieveAPIView):
    """
    Resolves a container from a legacy identifier and returns its metadata.

    Resolution strategy:
        1) If a finding aids entity exists with ``legacy_id`` matching the input,
           return that entity's container.
        2) Otherwise, if the identifier matches the pattern:
               ``HU_OSA_<fonds>_<subfonds>_<series>_<container_no>_<rest>``
           parse the parts and look up the container by archival unit numbers and
           container number.

    Authentication / Authorization:
        - BearerAuthentication or SessionAuthentication
        - Restricted to users in the ``Api`` group via APIGroupPermission

    Raises:
        - NotFound: when the legacy id cannot be resolved to a container.
    """

    swagger_schema = None
    serializer_class = ContainerDigitizedSerializer
    authentication_classes = [BearerAuthentication, SessionAuthentication]
    permission_classes = (APIGroupPermission, )

    def get_object(self):
        """
        Resolves and returns the container associated with the given legacy id.

        Returns:
            Container: The resolved container instance.

        Raises:
            NotFound: If no container can be resolved from the given legacy id.
        """
        legacy_id = self.kwargs['legacy_id']

        fa_objects = FindingAidsEntity.objects.filter(legacy_id=legacy_id)
        if fa_objects.count() > 0:
            fa_object = fa_objects.first()
            return fa_object.container
        else:
            if re.match(r'^HU_OSA_[0-9]+_[0-9]+_[0-9]*_[0-9]{4}', legacy_id):
                legacy_id = legacy_id.replace("HU_OSA_", "")
                fonds, subfonds, series, container_no, rest = legacy_id.split('_')
                container = get_object_or_404(
                    Container,
                    archival_unit__fonds=int(fonds),
                    archival_unit__subfonds=int(subfonds),
                    archival_unit__series=int(series),
                    container_no=int(container_no)
                )
                return container

        raise NotFound(detail="Error 404, page not found", code=404)
