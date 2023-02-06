# coding=utf-8
from django.db.models import Sum, Count
from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from authority.serializers import LanguageSerializer
from container.models import Container
from controlled_list.models import ReproductionRight
from finding_aids.models import FindingAidsEntity
from isaar.models import Isaar
from isad.models import Isad


class ArchivalUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = ArchivalUnit
        fields = ['title', 'title_original', 'title_full']


class IsaarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isaar
        fields = ['id', 'name']


class ArchivalUnitsDetailSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSerializer()
    title_original = serializers.SerializerMethodField()
    access_rights = serializers.SlugRelatedField(slug_field='statement', read_only=True)
    reproduction_rights = serializers.SlugRelatedField(slug_field='statement', queryset=ReproductionRight.objects.all())
    language = LanguageSerializer(many=True)
    creator = serializers.SlugRelatedField(slug_field='creator', many=True, read_only=True, source='isadcreator_set')
    isaar = IsaarSerializer(many=True)
    description_level = serializers.SerializerMethodField()
    extent_processed = serializers.SerializerMethodField()
    extent_processed_original = serializers.SerializerMethodField()
    digital_content_online = serializers.SerializerMethodField()

    def get_title_original(self, obj):
        return obj.archival_unit.title_original

    def get_description_level(self, obj):
        description_level_values = {'F': 'Fonds', 'SF': 'Subfonds', 'S': 'Series'}
        return description_level_values[obj.description_level]

    def get_extent_processed(self, obj):
        return self.get_extent(obj.archival_unit)

    def get_extent_processed_original(self, obj):
        return self.get_extent(obj.archival_unit, obj.original_locale.id if obj.original_locale else None)

    def get_digital_content_online(self, obj):
        return FindingAidsEntity.objects.filter(archival_unit=obj.archival_unit, digital_version_online=True).count()

    def get_extent(self, archival_unit, lang='EN'):
        extent = []
        total = 0

        if archival_unit.level == 'F':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds)
        elif archival_unit.level == 'SF':
            containers = Container.objects.filter(archival_unit__fonds=archival_unit.fonds,
                                                  archival_unit__subfonds=archival_unit.subfonds)
        else:
            containers = Container.objects.filter(archival_unit=archival_unit)

        containers = containers.values('carrier_type__type', 'carrier_type__type_original_language') \
            .annotate(width=Sum('carrier_type__width'), number=Count('id'))

        for c in containers:
            if lang == 'HU':
                extent.append(str(c['number']) + ' ' + c['carrier_type__type_original_language'] + ', ' +
                              str(round(c['width'] / 1000.00, 2)) + u' folyóméter')
            elif lang == 'PL':
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width'] / 1000.00, 2)) + u' metr bieżący')
            elif lang == 'IT':
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width'] / 1000.00, 2)) + u' metro lineare')
            else:
                extent.append(str(c['number']) + ' ' + c['carrier_type__type'] + ', ' +
                              str(round(c['width'] / 1000.00, 2)) + ' linear meters')
        return extent

    class Meta:
        model = Isad
        fields = '__all__'

