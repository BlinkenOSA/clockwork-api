from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import ArchivalUnitThemeSerializer, LocaleSerializer


class ArchivalUnitSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'reference_code', 'title', 'is_removable')


class ArchivalUnitSubfondsSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        series = ArchivalUnit.objects.filter(fonds=obj.fonds, subfonds=obj.subfonds, level='S')
        serializer = ArchivalUnitSeriesSerializer(series, many=True)
        if series.count() > 0:
            return serializer.data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitFondsSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        subfonds = ArchivalUnit.objects.filter(fonds=obj.fonds, level='SF')
        serializer = ArchivalUnitSubfondsSerializer(subfonds, many=True)
        if subfonds.count() > 0:
            return serializer.data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitReadSerializer(serializers.ModelSerializer):
    fonds_title = serializers.SerializerMethodField()
    fonds_acronym = serializers.SerializerMethodField()
    subfonds_title = serializers.SerializerMethodField()
    subfonds_acronym = serializers.SerializerMethodField()
    theme = ArchivalUnitThemeSerializer(many=True)
    original_locale = LocaleSerializer()

    def get_fonds_title(self, obj):
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return obj.parent.title
        else:
            return obj.parent.parent.title

    def get_fonds_acronym(self, obj):
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return obj.parent.acronym
        else:
            return obj.parent.parent.acronym

    def get_subfonds_title(self, obj):
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return None
        else:
            return obj.parent.title

    def get_subfonds_acronym(self, obj):
        if obj.level == 'F':
            return None
        elif obj.level == 'SF':
            return None
        else:
            return obj.parent.acronym

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