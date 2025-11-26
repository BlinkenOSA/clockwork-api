import json
import datetime
from rest_framework import serializers
from container.models import Container
from controlled_list.models import CarrierType


class DigitizationContainerLogSerializer(serializers.ModelSerializer):
    archival_unit_id = serializers.PrimaryKeyRelatedField(source='archival_unit', read_only=True)
    container_no = serializers.SerializerMethodField()
    duration = serializers.SerializerMethodField()
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())

    def get_container_no(self, obj):
        return "%s/%s" % (obj.archival_unit.reference_code, obj.container_no)

    def get_duration(self, obj):
        tech_md = obj.digital_version_technical_metadata
        if tech_md:
            tech_md = json.loads(tech_md)
            for stream in tech_md['streams']:
                if stream.get('codec_type') == 'video':
                    seconds = float(stream.get('duration'))
                    total_seconds = datetime.timedelta(seconds=seconds).total_seconds()
                    hours, remainder = divmod(total_seconds, 60 * 60)
                    minutes, seconds = divmod(remainder, 60)
                    return "%02d:%02d:%02d" % (hours, minutes, seconds)

    class Meta:
        model = Container
        fields = ('id', 'container_no', 'archival_unit_id', 'barcode', 'digital_version_exists',
                  'digital_version_research_cloud', 'digital_version_online',
                  'digital_version_research_cloud_path', 'digital_version_creation_date',
                  'duration', 'carrier_type', 'date_updated')


class DigitizationContainerDataSerializer(serializers.ModelSerializer):
    digital_version_technical_metadata = serializers.SerializerMethodField()

    def get_digital_version_technical_metadata(self, obj):
        return json.loads(obj.digital_version_technical_metadata) if obj.digital_version_technical_metadata else False

    class Meta:
        model = Container
        fields = ('digital_version_technical_metadata',)