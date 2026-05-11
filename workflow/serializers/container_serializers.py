from django.conf import settings
from rest_framework import serializers

from container.models import Container
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer
from workflow.serializers.digital_version_serializers import DigitalVersionSerializer

class ContainerBaseSerializer(serializers.ModelSerializer):
    """
    Serializer for digitized container metadata used in workflow endpoints.

    This serializer exposes technical and administrative metadata related to
    digitized archival containers, including:
        - barcode and container number
        - carrier type

    It is primarily used by long-term preservation and digitization workflows
    to exchange structured container data with external scripts.
    """

    archival_reference_code = serializers.SerializerMethodField()
    container_no = serializers.IntegerField(read_only=True)
    carrier_type = serializers.SerializerMethodField()

    def get_carrier_type(self, obj):
        """
        Returns the carrier type label for the container.

        Args:
            obj: Container instance.

        Returns:
            str: Human-readable carrier type.
        """
        return obj.carrier_type.type

    def get_archival_reference_code(self, obj):
        return "{}:{}".format(obj.archival_unit.reference_code, obj.container_no)

    class Meta:
        model = Container
        fields = [
            'archival_reference_code',
            'barcode',
            'container_no',
            'carrier_type',
        ]


class ContainerDigitizedSerializer(serializers.ModelSerializer):
    """
    Serializer for digitized container metadata used in workflow endpoints.

    This serializer exposes technical and administrative metadata related to
    digitized archival containers, including:
        - barcode and container number
        - carrier type
        - digital version status and storage information
        - associated archival unit hierarchy

    It is primarily used by long-term preservation and digitization workflows
    to exchange structured container data with external scripts.
    """

    archival_reference_code = serializers.SerializerMethodField()
    catalog_url = serializers.SerializerMethodField()
    archival_unit = ArchivalUnitSerializer(read_only=True)
    container = ContainerBaseSerializer(read_only=True, source='*')
    metadata = FindingAidsEntityReadSerializer(many=True, read_only=True, source='findingaidsentity_set')
    digital_versions = DigitalVersionSerializer(many=True, read_only=True)
    level = serializers.SerializerMethodField()

    def get_level(self, obj):
        return 'Container'

    def get_archival_reference_code(self, obj):
        return "{}:{}".format(obj.archival_unit.reference_code, obj.container_no)

    def get_catalog_url(self, obj):
        catalog_url = getattr(settings, 'CATALOG_URL')
        if obj.archival_unit.isad.published:
            return '{}/{}?tab=content&start={}'.format(catalog_url, obj.archival_unit.isad.catalog_id ,obj.container_no)
        else:
            return 'N/A'

    class Meta:
        model = Container
        fields = [
            'archival_reference_code',
            'level',
            'catalog_url',
            'archival_unit',
            'container',
            'metadata',
            'digital_versions'
        ]