from rest_framework import serializers

from digitization.models import DigitalVersion


class DigitalVersionSerializer(serializers.ModelSerializer):

    class Meta:
        model = DigitalVersion
        fields = [
            'id',
            'identifier',
            'level',
            'filename',
            'label',
            'available_research_cloud',
            'available_online',
            'research_cloud_path'
        ]