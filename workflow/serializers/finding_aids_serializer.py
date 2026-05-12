from django.conf import settings
from rest_framework import serializers

from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer
from workflow.serializers.container_serializers import ContainerBaseSerializer
from workflow.serializers.digital_version_serializers import DigitalVersionSerializer


class FindingAidsDigitizedSerializer(serializers.ModelSerializer):
    """
    Serializer for digitized finding aids entity metadata used in workflow endpoints.

    This serializer exposes technical and administrative metadata related to
    digitized finding aids entities, including:
        - barcode and container number
        - carrier type
        - digital version status and storage information
        - associated archival unit hierarchy

    It is primarily used by long-term preservation and digitization workflows
    to exchange structured container data with external scripts.
    """

    catalog_url = serializers.SerializerMethodField()
    archival_unit = ArchivalUnitSerializer(read_only=True, source='container.archival_unit')
    container = ContainerBaseSerializer(read_only=True)
    metadata = FindingAidsEntityReadSerializer(read_only=True, source='*')
    digital_versions = DigitalVersionSerializer(many=True, read_only=True)
    level = serializers.SerializerMethodField()

    def get_level(self, obj):
        return 'Folder / Item'

    def get_catalog_url(self, obj):
        catalog_url = getattr(settings, 'CATALOG_URL')
        if obj.published:
            return "{}/{}".format(catalog_url, obj.catalog_id)

    class Meta:
        model = FindingAidsEntity
        fields = [
            'archival_reference_code',
            'level',
            'catalog_url',
            'archival_unit',
            'container',
            'digital_versions',
            'metadata'
        ]
