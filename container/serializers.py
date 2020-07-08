import json
import datetime
from rest_framework import serializers

from container.models import Container
from controlled_list.models import CarrierType
from finding_aids.models import FindingAidsEntity


class ContainerReadSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())

    class Meta:
        model = Container
        fields = '__all__'


class ContainerWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        exclude = ('container_no', )


class ContainerListSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    reference_code = serializers.SerializerMethodField(source='container_no')
    total_number = serializers.SerializerMethodField()
    total_published_number = serializers.SerializerMethodField()

    def get_total_number(self, obj):
        return FindingAidsEntity.objects.filter(container=obj).exclude(is_template=True).count()

    def get_total_published_number(self, obj):
        return FindingAidsEntity.objects.filter(container=obj, published=True).exclude(is_template=True).count()

    def get_reference_code(self, obj):
        return "%s/%s" % (obj.archival_unit.reference_code, obj.container_no)

    class Meta:
        model = Container
        fields = ('id', 'reference_code', 'barcode', 'carrier_type', 'total_number', 'total_published_number',
                  'is_removable')


class ContainerSelectSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    reference_code = serializers.SerializerMethodField(source='container_no')
    digital_version_duration = serializers.SerializerMethodField(source='digital_version_technical_metadata')

    def get_reference_code(self, obj):
        return "%s/%s" % (obj.archival_unit.reference_code, obj.container_no)

    def get_digital_version_duration(self, obj):
        if obj.digital_version_technical_metadata:
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
