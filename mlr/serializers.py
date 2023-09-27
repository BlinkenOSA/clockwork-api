from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from controlled_list.models import CarrierType
from mlr.models import MLREntity, MLREntityLocation


class MLRListSerializer(serializers.ModelSerializer):
    series = serializers.SlugRelatedField(slug_field='reference_code', queryset=ArchivalUnit.objects.all())
    quantity = serializers.SerializerMethodField()
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    size = serializers.SerializerMethodField()
    mrss = serializers.SerializerMethodField()

    def get_quantity(self, obj):
        return obj.get_count()

    def get_size(self, obj):
        return obj.get_size()

    def get_mrss(self, obj):
        return obj.get_locations()

    class Meta:
        model = MLREntity
        fields = ['id', 'series', 'quantity', 'carrier_type', 'size', 'mrss']


class MLREntityLocationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MLREntityLocation
        fields = ['id', 'building', 'module', 'row', 'section', 'shelf']


class MLREntitySerializer(WritableNestedModelSerializer):
    series_name = serializers.SerializerMethodField()
    locations = MLREntityLocationsSerializer(many=True)

    def get_series_name(self, obj):
        return obj.series.title_full

    class Meta:
        model = MLREntity
        fields = ['id', 'series', 'series_name', 'carrier_type', 'locations', 'notes']