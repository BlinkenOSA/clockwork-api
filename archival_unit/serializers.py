from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import ArchivalUnitThemeSerializer, LocaleSerializer


class ArchivalUnitReadSerializer(serializers.ModelSerializer):
    theme = ArchivalUnitThemeSerializer(many=True)
    original_locale = LocaleSerializer()

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitWriteSerializer(UserDataSerializerMixin, serializers.ModelSerializer):
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

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class ArchivalUnitSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'reference_code', 'title', 'title_full')