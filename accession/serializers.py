from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from accession.models import Accession, AccessionItem, AccessionMethod, AccessionCopyrightStatus
from archival_unit.serializers import ArchivalUnitSelectSerializer, ArchivalUnitReadSerializer
from clockwork_api.fields import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin


class AccessionMethodSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionMethod
        fields = '__all__'


class AccessionCopyrightStatusSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionCopyrightStatus
        fields = '__all__'


class AccessionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AccessionItem
        fields = 'id', 'quantity', 'container', 'content'


class AccessionReadSerializer(serializers.ModelSerializer):
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionListSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitReadSerializer()

    class Meta:
        model = Accession
        fields = ['id', 'seq', 'transfer_date', 'title', 'archival_unit']


class AccessionWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    transfer_date = ApproximateDateSerializerField()
    creation_date_from = ApproximateDateSerializerField(required=False)
    creation_date_to = ApproximateDateSerializerField(required=False)
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    def validate(self, data):
        creation_date_from = data.get('creation_date_from', None)
        creation_date_to = data.get('creation_date_to', None)
        if creation_date_to:
            if creation_date_from > creation_date_to:
                raise ValidationError("Date from value is bigger than date to value.")
        return data

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionSelectSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSelectSerializer()

    class Meta:
        model = Accession
        fields = ('id', 'transfer_date', 'seq',
                  'archival_unit', 'archival_unit_legacy_number', 'archival_unit_legacy_name')