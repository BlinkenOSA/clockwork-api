import json
from rest_framework import serializers
from controlled_list.models import PrimaryType
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityLogSerializer(serializers.ModelSerializer):
    """
    Serializer for finding aids digitization log entries.

    Used by digitization dashboards and activity views to display the
    digitization status of finding aids entities, including availability
    flags and primary type classification.
    """

    primary_type = serializers.SlugRelatedField(slug_field='type', queryset=PrimaryType.objects.all())

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'digital_version_exists',
                  'digital_version_research_cloud', 'digital_version_online',
                  'digital_version_research_cloud_path', 'digital_version_creation_date',
                  'primary_type')


class FindingAidsEntityDataSerializer(serializers.ModelSerializer):
    """
    Serializer exposing parsed technical metadata for a finding aids entity.

    Intended for clients that need direct access to the structured
    digitization metadata rather than the raw JSON string stored on the model.
    """

    digital_version_technical_metadata = serializers.SerializerMethodField()

    def get_digital_version_technical_metadata(self, obj):
        """
        Returns the technical metadata as a parsed JSON object.

        Returns False when no technical metadata is available.
        """
        return json.loads(obj.digital_version_technical_metadata) if obj.digital_version_technical_metadata else False

    class Meta:
        model = FindingAidsEntity
        fields = ('digital_version_technical_metadata',)