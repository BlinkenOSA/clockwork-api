from rest_framework import serializers

from isad.models import Isad


class ISADAMSIndexerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isad
        fields = ('id', 'reference_code', 'title', 'published')
