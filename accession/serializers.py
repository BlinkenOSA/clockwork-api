from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from accession.models import Accession, AccessionItem, AccessionMethod, AccessionCopyrightStatus
from archival_unit.serializers import ArchivalUnitSelectSerializer
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


class AccessionWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    transfer_date = ApproximateDateSerializerField()
    creation_date_from = ApproximateDateSerializerField()
    creation_date_to = ApproximateDateSerializerField()
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionSelectSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSelectSerializer()

    class Meta:
        model = Accession
        fields = ('id', 'transfer_date', 'seq',
                  'archival_unit', 'archival_unit_legacy_number', 'archival_unit_legacy_name')