from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from controlled_list.serializers import ArchivalUnitThemeSerializer, LocaleSerializer


class ArchivalUnitReadSerializer(serializers.ModelSerializer):
    theme = ArchivalUnitThemeSerializer(many=True)
    original_locale = LocaleSerializer()

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitWriteSerializer(serializers.ModelSerializer):
    reference_code = serializers.CharField(required=False)
    reference_code_id = serializers.CharField(required=False)

    def validate_status(self, value):
        if value not in ['Final', 'Draft']:
            raise ValidationError("Status should be either: 'Final' or 'Draft'")
        return value

    def validate_level(self, value):
        if value not in ['F', 'SF', 'S']:
            raise ValidationError("Level should be either: 'Fonds', 'Subfonds', 'Series'")
        return value

    def create(self, validated_data):
        if 'user' not in validated_data:
            validated_data['user_created'] = self.context['request'].user
        return super(ArchivalUnitWriteSerializer, self).create(validated_data)

    def update(self, instance, validated_data):
        if 'user' not in validated_data:
            validated_data['user_updated'] = self.context['request'].user
            validated_data['date_updated'] = timezone.now()
        return super(ArchivalUnitWriteSerializer, self).update(validated_data)

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'reference_code', 'title', 'title_full')