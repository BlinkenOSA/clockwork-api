from rest_framework import serializers


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