from django.core.exceptions import ObjectDoesNotExist
from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from container.models import Container
from mlr.models import MLREntity
from research.models import RequestItem, Request


class RequestListSerializer(serializers.ModelSerializer):
    researcher = serializers.SlugRelatedField(slug_field='name', read_only=True, source='request.researcher')
    created_date = serializers.SlugRelatedField(slug_field='created_date', read_only=True, source='request')
    request_date = serializers.SlugRelatedField(slug_field='request_date', read_only=True, source='request')
    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True, source='container.carrier_type')
    archival_reference_number = serializers.SerializerMethodField()
    mlr = serializers.SerializerMethodField()
    has_digital_version = serializers.BooleanField(source='container.has_digital_version')
    digital_version_barcode = serializers.SerializerMethodField()

    def get_mlr(self, obj):
        if obj.item_origin == 'FA':
            same_archival_request = RequestItem.objects.filter(
                item_origin='FA', container=obj.container).exclude(id=obj.id)
            if same_archival_request.filter(status='3').exists():
                return 'Currently used'
            if same_archival_request.filter(status='4').exists():
                return 'Waiting to be reshelved'

        else:
            same_library_request = RequestItem.objects.filter(
                identifier=obj.identifier).exclude(id=obj.id, item_origin='FA')
            if same_library_request.filter(status='3').exists():
                return 'Currently used'
            if same_library_request.filter(status='4').exists():
                return 'Waiting to be reshelved'

        if obj.item_origin == 'FA':
            series = obj.container.archival_unit
            carrier_type = obj.container.carrier_type
            try:
                mlr = MLREntity.objects.get(series=series, carrier_type=carrier_type)
                return mlr.get_locations()
            except ObjectDoesNotExist:
                return ''

        return 'Library Record'

    def get_digital_version_barcode(self, obj):
        if obj.container.has_digital_version:
            return obj.container.barcode
        else:
            return None

    def get_archival_reference_number(self, obj):
        if obj.item_origin == 'FA':
            return "%s:%s" % (obj.container.archival_unit.reference_code, obj.container.container_no)
        else:
            return ''

    class Meta:
        model = RequestItem
        fields = '__all__'


class ContainerListSerializer(serializers.ModelSerializer):
    container_label = serializers.SerializerMethodField()

    def get_container_label(self, obj):
        return "%s (%s)" % (obj.container_no, obj.carrier_type.type)

    class Meta:
        model = Container
        fields = ('id', 'container_label')


class RequestItemCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestItem
        fields = ('id', 'item_origin', 'container', 'identifier', 'title')


class RequestCreateSerializer(WritableNestedModelSerializer):
    request_items = RequestItemCreateSerializer(many=True, source='requestitem_set')

    class Meta:
        model = Request
        fields = ('researcher', 'request_date', 'request_items')


class RequestItemWriteSerializer(serializers.ModelSerializer):
    researcher = serializers.CharField(source='request.researcher.name', read_only=True)
    request_date = serializers.CharField(source='request.request_date', read_only=True)
    archival_unit = serializers.SerializerMethodField()

    def get_archival_unit(self, obj):
        return obj.container.archival_unit.id

    class Meta:
        model = RequestItem
        fields = ('id', 'archival_unit', 'researcher', 'request_date', 'item_origin', 'container', 'identifier', 'title')