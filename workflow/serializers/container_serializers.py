from rest_framework import serializers

from container.models import Container
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer


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

    container_no = serializers.IntegerField(read_only=True)
    carrier_type = serializers.SerializerMethodField()
    archival_unit = ArchivalUnitSerializer(read_only=True)

    def get_carrier_type(self, obj):
        """
        Returns the carrier type label for the container.

        Args:
            obj: Container instance.

        Returns:
            str: Human-readable carrier type.
        """
        return obj.carrier_type.type

    class Meta:
        model = Container
        fields = [
            'barcode',
            'carrier_type',
            'container_no',
            'digital_version_exists',
            'digital_version_research_cloud',
            'digital_version_research_cloud_path',
            'digital_version_technical_metadata',
            'digital_version_creation_date',
            'archival_unit',
        ]
