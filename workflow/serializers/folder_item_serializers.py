from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSerializer(serializers.ModelSerializer):
    theme = serializers.StringRelatedField(many=True)
    level = serializers.SerializerMethodField()

    def get_level(self, value):
        if value == 'F':
            return 'Fonds'
        elif value == 'SF':
            return 'Subfonds'
        else:
            return 'Series'

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class FADigitizedSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSerializer(read_only=True)

    class Meta:
        model = FindingAidsEntity
        fields = ['archival_unit', 'title', 'folder_no', 'sequence_no', 'catalog_id', 'archival_reference_code']
