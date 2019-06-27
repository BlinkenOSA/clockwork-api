import json
import datetime
from rest_framework import serializers

from container.models import Container
from controlled_list.models import CarrierType
from controlled_list.serializers import CarrierTypeSelectSerializer


class ContainerReadSerializer(serializers.ModelSerializer):
    carrier_type = CarrierTypeSelectSerializer()

    class Meta:
        model = Container
        fields = '__all__'


class ContainerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = '__all__'


class ContainerSelectSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    reference_code = serializers.SerializerMethodField(source='container_no')
    digital_version_duration = serializers.SerializerMethodField(source='digital_version_technical_metadata')

    def get_reference_code(self, obj):
        return "%s/%s" % (obj.archival_unit.reference_code, obj.container_no)

    def get_digital_version_duration(self, obj):
        tech_md = json.loads(obj.digital_version_technical_metadata)
        for stream in tech_md['streams']:
            if stream.get('codec_type') == 'video':
                seconds = float(stream.get('duration'))
                total_seconds = datetime.timedelta(seconds=seconds).total_seconds()
                hours, remainder = divmod(total_seconds, 60 * 60)
                minutes, seconds = divmod(remainder, 60)
                return "%02d:%02d:%02d" % (hours, minutes, seconds)

    class Meta:
        model = Container
        fields = ('id', 'reference_code', 'digital_version_creation_date',
                  'digital_version_duration', 'barcode', 'carrier_type')
