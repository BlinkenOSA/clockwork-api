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

class DigitalObjectInfoResponseSerializer(serializers.Serializer):
    doi = serializers.CharField(label='Digital Object Identifier', help_text='Digital Object Identifier', required=False)
    container_reference_code = serializers.CharField(
        label='Container Reference Code', 
        help_text='example: HU OSA 386-1-1:1, only exists if the digital object is based on a container', 
        required=False
    )
    fa_entity_reference_code = serializers.CharField(
        label='Folder / Item Reference Code', 
        help_text='example: HU OSA 386-1-1:1/1, only exists if the digital object is based on a folder / item record', 
        required=False
    )
    primary_type = serializers.CharField(
        label='Primary Type',
        help_text='Primary Type of the identified record. Either Textual, Moving Image, Still Image or Audio',
        required=False)
    level = serializers.CharField(
        label='Level',
        help_text='Explanatory text of the level of the identified record. Example: 1st folder in 1st container.',
        required=False)
    access_copy_to_catalog = AccessCopySerializer(
        label='Access Copy',
        help_text='Information about where to upload the access copy of the digital object.',
        required=False)

class DigitalObjectUpsertResponseSerializer(serializers.Serializer):
    digital_version_id = serializers.IntegerField(
        label='Digital Version Object ID',
        help_text='The ID of the record in the digital_version table of the AMS database',
        required=False)
    filename = serializers.CharField(
        label='Filename',
        help_text='The name of the file uploaded and set as the access copy',
        required=False)