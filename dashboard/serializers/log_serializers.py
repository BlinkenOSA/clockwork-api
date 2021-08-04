from rest_framework import serializers
from rest_framework.serializers import ModelSerializer

from accession.models import Accession
from archival_unit.models import ArchivalUnit
from archival_unit.serializers import ArchivalUnitSelectSerializer
from container.models import Container
from controlled_list.models import CarrierType
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


class AccessionLogSerializer(ModelSerializer):
    archival_unit = ArchivalUnitSelectSerializer()

    class Meta:
        model = Accession
        fields = ('id', 'transfer_date', 'seq', 'archival_unit',
                  'archival_unit_legacy_number', 'archival_unit_legacy_name', 'user_created')


class ArchivalUnitLogSerializer(ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'reference_code', 'title_full', 'date_created', 'user_created')


class IsadLogSerializer(ModelSerializer):
    class Meta:
        model = Isad
        fields = ('id', 'reference_code', 'title', 'date_created', 'user_created', 'date_updated', 'user_updated')


class FindingAidsLogSerializer(ModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'title', 'date_created', 'user_created', 'date_updated', 'user_updated')


class DigitizationLogSerializer(ModelSerializer):
    container_no = serializers.SerializerMethodField()
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())

    def get_container_no(self, obj):
        return "%s/%s" % (obj.archival_unit.reference_code, obj.container_no)

    class Meta:
        model = Container
        fields = ('id', 'container_no', 'barcode', 'digital_version_exists', 'digital_version_creation_date', 'carrier_type')
