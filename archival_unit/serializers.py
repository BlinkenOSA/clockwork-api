from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSeriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'reference_code', 'title', 'is_removable')


class ArchivalUnitSubfondsSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        if obj.children.count() > 0:
            return ArchivalUnitSeriesSerializer(obj.children, many=True).data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitFondsSerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    def get_children(self, obj):
        if obj.children.count() > 0:
            return ArchivalUnitSubfondsSerializer(obj.children, many=True).data
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'is_removable')


class ArchivalUnitPreCreateSerializer(serializers.ModelSerializer):
    parent = serializers.IntegerField(source='pk')
    fonds_title = serializers.SerializerMethodField()
    fonds_acronym = serializers.SerializerMethodField()
    subfonds_title = serializers.SerializerMethodField()
    subfonds_acronym = serializers.SerializerMethodField()
    level = serializers.SerializerMethodField()

    def get_fonds_title(self, obj):
        if obj.level == 'F':
            return obj.title
        elif obj.level == 'SF':
            return obj.parent.title

    def get_fonds_acronym(self, obj):
        if obj.level == 'F':
            return obj.acronym
        elif obj.level == 'SF':
            return obj.parent.acronym

    def get_subfonds_title(self, obj):
        if obj.level == 'SF':
            return obj.title
        elif obj.level == 'S':
            return obj.parent.title

    def get_subfonds_acronym(self, obj):
        if obj.level == 'SF':
            return obj.acronym
        elif obj.level == 'S':
            return obj.parent.acronym

    def get_level(self, obj):
        if obj.level == 'F':
            return 'SF'
        elif obj.level == 'SF':
            return 'S'

    class Meta:
        model = ArchivalUnit
        fields = ('parent',
                  'fonds', 'fonds_title', 'fonds_acronym',
                  'subfonds', 'subfonds_title', 'subfonds_acronym',
                  'series', 'level')


class ArchivalUnitReadSerializer(serializers.ModelSerializer):
    fonds_title = serializers.SerializerMethodField()
    fonds_acronym = serializers.SerializerMethodField()
    subfonds_title = serializers.SerializerMethodField()
    subfonds_acronym = serializers.SerializerMethodField()

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
    container_count = serializers.SerializerMethodField()
    folder_count = serializers.SerializerMethodField()

    def get_container_count(self, obj):
        if obj.level == 'S':
            return Container.objects.filter(archival_unit=obj).count()
        else:
            return None

    def get_folder_count(self, obj):
        if obj.level == 'S':
            return FindingAidsEntity.objects.filter(archival_unit=obj).exclude(is_template=True).count()
        else:
            return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'reference_code', 'title', 'title_full', 'container_count', 'folder_count')
