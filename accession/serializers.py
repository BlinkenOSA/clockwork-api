from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from accession.models import Accession, AccessionItem, AccessionMethod, AccessionCopyrightStatus
from archival_unit.serializers import ArchivalUnitSelectSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import BuildingSelectSerializer
from donor.serializers import DonorSelectSerializer


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
    method = AccessionMethodSelectSerializer()
    building = BuildingSelectSerializer()
    archival_unit = ArchivalUnitSelectSerializer()
    donor = DonorSelectSerializer()
    copyright_status = AccessionCopyrightStatusSelectSerializer()
    items = AccessionItemSerializer(many=True, source='accessionitem_set')

    class Meta:
        model = Accession
        fields = '__all__'


class AccessionWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
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