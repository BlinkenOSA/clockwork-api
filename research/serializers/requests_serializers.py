from django.core.exceptions import ObjectDoesNotExist
from rest_framework import serializers

from container.models import Container
from mlr.models import MLREntity
from research.models import RequestItem


class RequestListSerializer(serializers.ModelSerializer):
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request.researcher')
    created_date = serializers.SlugRelatedField(slug_field='created_date', read_only=True, source='request')
    request_date = serializers.SlugRelatedField(slug_field='request_date', read_only=True, source='request')
    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True, source='container.carrier_type')
    mlr = serializers.SerializerMethodField()

    def get_mlr(self, obj):
        if obj.item_origin == 'FA':
            series = obj.container.archival_unit
            carrier_type = obj.container.carrier_type
            try:
                mlr = MLREntity.objects.get(series=series, carrier_type=carrier_type)
                return mlr.get_locations()
            except ObjectDoesNotExist:
                return ''
        return 'Library Record'

    class Meta:
        model = RequestItem
        fields = '__all__'


class ContainerListSerializer(serializers.ModelSerializer):
    reference_code = serializers.SerializerMethodField()

    def get_reference_code(self, obj):
        return "%s:%s" % (obj.archival_unit.reference_code, obj.container_no)

    class Meta:
        model = Container
        fields = ('id', 'reference_code')
