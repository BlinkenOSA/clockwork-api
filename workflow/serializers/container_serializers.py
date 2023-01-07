from rest_framework import serializers

from container.models import Container
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer


class ContainerDigitizedSerializer(serializers.ModelSerializer):
    container_no = serializers.IntegerField(read_only=True)
    carrier_type = serializers.SerializerMethodField()
    archival_unit = ArchivalUnitSerializer(read_only=True)

    def get_carrier_type(self, obj):
        return obj.carrier_type.type

    class Meta:
        model = Container
        fields = ['barcode', 'carrier_type', 'container_no', 'digital_version_exists',
                  'digital_version_technical_metadata', 'digital_version_creation_date', 'archival_unit']

