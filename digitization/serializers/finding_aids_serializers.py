import json
from rest_framework import serializers
from container.models import Container
from controlled_list.models import PrimaryType
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityLogSerializer(serializers.ModelSerializer):
    primary_type = serializers.SlugRelatedField(slug_field='type', queryset=PrimaryType.objects.all())

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'digital_version_exists',
                  'digital_version_research_cloud', 'digital_version_online',
                  'digital_version_research_cloud_path', 'digital_version_creation_date',
                  'primary_type')


class FindingAidsEntityDataSerializer(serializers.ModelSerializer):
    digital_version_technical_metadata = serializers.SerializerMethodField()

    def get_digital_version_technical_metadata(self, obj):
        return json.loads(obj.digital_version_technical_metadata) if obj.digital_version_technical_metadata else False

    class Meta:
        model = FindingAidsEntity
        fields = ('digital_version_technical_metadata',)