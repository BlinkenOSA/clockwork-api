from rest_framework import serializers

from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityReadSerializer
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer
from workflow.serializers.container_serializers import ContainerBaseSerializer
from workflow.serializers.digital_version_serializers import DigitalVersionSerializer


class DigitalObjectUpsertRequestSerializer(serializers.Serializer):
    technical_metadata = serializers.IntegerField(
        label='Technical Metadata',
        help_text='Extracted technical metadata, only required for master files.',
        required=False
    )


class DigitalObjectUpsertResponseSerializer(serializers.Serializer):
    """
    Serializer for digital object upsert responses.

    Returned after creating or updating a digital object record
    in the AMS system.

    Contains identifiers for tracking the stored digital asset.
    """

    digital_version_id = serializers.IntegerField(
        label='Digital Version Object ID',
        help_text='ID of the record in the digital_version table',
        required=False
    )

    action = serializers.CharField(
        label='Action',
        help_text='Shows if the Digital Version Object was created or updated',
        required=False
    )

    identifier = serializers.CharField(
        label='Digital Object Identifier',
        help_text='Digital Object Identifier',
        required=False
    )

    filename = serializers.CharField(
        label='Filename',
        help_text='Name of the uploaded file',
        required=False
    )


class DigitalVersionInfoSerializer(serializers.Serializer):
    """
    Serializer for digital object information responses.

    Returned after resolving a filename to an archival unit, container, or finding aids entity.

    Contains identifiers and metadata for the resolved object.
    """
    archival_reference_code = serializers.CharField(
        label='Archival Reference Code',
        help_text='Archival Reference Code of the resolved object',
        required=False
    )
    level = serializers.CharField(
        label='Level',
        help_text='"Folder / Item" or "Container" depending on the type of object resolved from the filename',
        required=False
    )
    catalog_url = serializers.CharField(
        label='Catalog URL',
        help_text='URL to the object in the catalog',
        required=False
    )
    archival_unit = ArchivalUnitSerializer(read_only=True)
    container = ContainerBaseSerializer(read_only=True, source='*')
    metadata = FindingAidsEntityReadSerializer(many=True, read_only=True)
    digital_versions = DigitalVersionSerializer(many=True, read_only=True)
