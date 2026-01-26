from rest_framework import serializers


class AccessCopySerializer(serializers.Serializer):
    """
    Serializer for access copy delivery configuration.

    Describes where and how an access copy and its thumbnail
    should be transferred on the destination server.
    """

    target_server = serializers.CharField(
        label='Target Server',
        help_text='IP Address of the destination server',
        required=False
    )

    target_path = serializers.CharField(
        label='Target Path',
        help_text='The absolute path of the access copy on the destination server',
        required=False
    )

    thumbnail_path = serializers.CharField(
        label='Thumbnail Path',
        help_text='The absolute path of the thumbnail image on the destination server',
        required=False
    )


class ArchivalUnitSerializer(serializers.Serializer):
    """
    Serializer for basic archival unit identification metadata.

    Used within workflow responses to describe fonds, subfonds,
    or series-level units related to a digital object.
    """

    reference_number = serializers.CharField(
        label='Reference Number',
        help_text='The reference number of the archival unit',
        required=False
    )

    title = serializers.CharField(
        label='Title',
        help_text='The title of the archival unit',
        required=False
    )

    catalog_id = serializers.CharField(
        label='Catalog ID',
        help_text='URL of the archival unit in the archival catalog.',
        required=False
    )


class ArchivalUnitWrapperSerializer(serializers.Serializer):
    """
    Wrapper serializer for hierarchical archival unit information.

    Groups fonds, subfonds, and series metadata into a structured
    hierarchy for workflow API responses.
    """

    fonds = ArchivalUnitSerializer(
        label='Fonds',
        help_text='Information about the fonds.',
        required=False
    )

    subfonds = ArchivalUnitSerializer(
        label='Subfonds',
        help_text='Information about the subfonds.',
        required=False
    )

    series = ArchivalUnitSerializer(
        label='Series',
        help_text='Information about the series.',
        required=False
    )


class DigitalObjectInfoResponseSerializer(serializers.Serializer):
    """
    Serializer for digital object metadata responses.

    Used by workflow services to return descriptive, technical,
    and access-related information about a digital object.

    Includes:
        - Persistent identifiers
        - Descriptive metadata
        - Archival hierarchy
        - Access copy delivery configuration
    """

    doi = serializers.CharField(
        label='Digital Object Identifier',
        help_text='Digital Object Identifier',
        required=False
    )

    reference_code = serializers.CharField(
        label='Reference Code',
        help_text=(
            'Example: HU OSA 386-1-1:1 when based on a container record, '
            'or HU OSA 386-1-1:1/1 when based on a folder/item record'
        ),
        required=False
    )

    level = serializers.CharField(
        label='Level',
        help_text='Identified level: container, folder, or item',
        required=False
    )

    primary_type = serializers.CharField(
        label='Primary Type',
        help_text='Textual, Moving Image, Still Image, or Audio',
        required=False
    )

    title = serializers.CharField(
        label='Title',
        help_text=(
            'Title of the digital object. Either the folder/item title '
            'or the carrier type and container number.'
        ),
        required=False
    )

    catalog_id = serializers.CharField(
        label='Catalog ID',
        help_text='URL of the record in the archival catalog.',
        required=False
    )

    access_copy_to_catalog = AccessCopySerializer(
        label='Access Copy',
        help_text='Information about where to upload the access copy.',
        required=False
    )

    archival_unit = ArchivalUnitWrapperSerializer()


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

    filename = serializers.CharField(
        label='Filename',
        help_text='Name of the uploaded access copy file',
        required=False
    )
