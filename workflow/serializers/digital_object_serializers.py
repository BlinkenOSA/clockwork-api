from rest_framework import serializers
from rest_framework.serializers import Serializer


class AccessCopySerializer(serializers.Serializer):
    target_server = serializers.CharField(
        label='Target Server',
        help_text='IP Address of the destination server',
        required=False)
    target_path =  serializers.CharField(
        label='Target Path',
        help_text='The absolute path of the access copy on the destination server',
        required=False)
    thumbnail_path = serializers.CharField(
        label='Thumbnail Path',
        help_text='The absolute path of the thumbnail image on the destination server',
        required=False)

class ArchivalUnitSerializer(serializers.Serializer):
    reference_number = serializers.CharField(
        label='Refernece Number',
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
    doi = serializers.CharField(label='Digital Object Identifier', help_text='Digital Object Identifier', required=False)
    reference_code = serializers.CharField(
        label='Reference Code',
        help_text='example: HU OSA 386-1-1:1 when the digital object is based on a container record, or HU OSA 386-1-1:1/1 when the digital object is based on a folder / item record',
        required=False
    )
    level = serializers.CharField(
        label='Level',
        help_text='The identified level of the submitted record. Either: container, folder, item',
        required=False)
    primary_type = serializers.CharField(
        label='Primary Type',
        help_text='Primary Type of the submitted record. Either: Textual, Moving Image, Still Image or Audio',
        required=False)
    title = serializers.CharField(
        label='Title',
        help_text='Title of the digital object. Either the title of the folder/item record, or the carrier type and the '
                  'number of the container.',
        required=False)
    catalog_id = serializers.CharField(
        label='Catalog ID',
        help_text='URL of the record in the archival catalog.',
        required=False)
    access_copy_to_catalog = AccessCopySerializer(
        label='Access Copy',
        help_text='Information about where to upload the access copy of the digital object.',
        required=False)
    archival_unit = ArchivalUnitWrapperSerializer()

class DigitalObjectUpsertResponseSerializer(serializers.Serializer):
    digital_version_id = serializers.IntegerField(
        label='Digital Version Object ID',
        help_text='The ID of the record in the digital_version table of the AMS database',
        required=False)
    filename = serializers.CharField(
        label='Filename',
        help_text='The name of the file uploaded and set as the access copy',
        required=False)