from hashids import Hashids
from rest_framework import serializers

from isad.models import Isad


class ISADCatalogIndexerSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    ams_id = serializers.IntegerField(source='archival_unit.id')
    record_origin = serializers.SerializerMethodField()
    record_origin_facet = serializers.SerializerMethodField(method_name='get_record_origin')
    archival_level = serializers.SerializerMethodField()
    archival_level_facet = serializers.SerializerMethodField(method_name='get_archival_level')
    reference_code_sort = serializers.CharField(source='reference_code')
    archival_reference_number_search = serializers.CharField(source='reference_code')
    title_e = serializers.CharField(source='title')
    title_search = serializers.CharField(source='title')
    title_sort = serializers.CharField(source='title')
    description_level = serializers.SerializerMethodField()
    description_level_facet = serializers.SerializerMethodField(method_name='get_description_level')
    date_created = serializers.SerializerMethodField(method_name='get_date_created_display')
    date_created_search = serializers.SerializerMethodField(method_name='get_date_created_search')
    date_created_facet = serializers.SerializerMethodField(method_name='get_date_created_search')
    fonds = serializers.IntegerField(source='archival_unit.fonds')
    fonds_sort = serializers.IntegerField(source='archival_unit.fonds')
    subfonds = serializers.IntegerField(source='archival_unit.subfonds')
    subfonds_sort = serializers.IntegerField(source='archival_unit.subfonds')
    series = serializers.IntegerField(source='archival_unit.series')
    series_sort = serializers.IntegerField(source='archival_unit.series')
    fonds_name = serializers.SerializerMethodField()
    subfonds_name = serializers.SerializerMethodField()
    scope_and_content_abstract_search = serializers.CharField(source='scope_and_content_abstract')
    scope_and_content_narrative_search = serializers.CharField(source='scope_and_content_narrative')
    archival_history_search = serializers.CharField(source='archival_history')
    publication_note_search = serializers.CharField(source='publication_note')
    primary_type = serializers.SerializerMethodField()
    primary_type_facet = serializers.SerializerMethodField(method_name='get_primary_type')
    language = serializers.SerializerMethodField()
    language_facet = serializers.SerializerMethodField(method_name='get_language')
    creator = serializers.SerializerMethodField()
    creator_facet = serializers.SerializerMethodField(method_name='get_creator')
    archival_unit_theme = serializers.SerializerMethodField()
    archival_unit_theme_facet = serializers.SerializerMethodField(method_name='get_archival_unit_theme')

    def get_id(self, obj):
        hashids = Hashids(salt="osaarchives", min_length=8)
        return hashids.encode(
            obj.archival_unit.fonds * 1000000 +
            obj.archival_unit.subfonds * 1000 +
            obj.archival_unit.series
        )

    def get_record_origin(self, obj):
        return 'Archives'

    def get_archival_level(self, obj):
        return 'Archival Unit'

    def get_description_level(self, obj):
        levels = {
            'F': 'Fonds',
            'SF': 'Subfonds',
            'S': 'Series'
        }
        return levels[obj.description_level]

    def get_date_created_search(self, obj):
        date = []
        if obj.year_to:
            for year in range(obj.year_from, obj.year_to + 1):
                date.append(year)
        else:
            date.append(str(obj.year_from))
        return date

    def get_date_created_display(self, obj):
        if obj.year_from > 0:
            date = str(obj.year_from)

            if obj.year_to:
                if obj.year_from != obj.year_to:
                    date = date + " - " + str(obj.year_to)
        else:
            date = ""
        return date

    def get_fonds_name(self, obj):
        if obj.description_level == 'F':
            return obj.archival_unit.get_fonds().title_full
        else:
            return None

    def get_subfonds_name(self, obj):
        if obj.description_level == 'SF':
            return obj.archival_unit.get_subfonds().title_full
        else:
            return None

    def get_primary_type(self, obj):
        return 'Archival Unit'

    def get_language(self, obj):
        return list(map(lambda l: l.language, obj.language.all()))

    def get_creator(self, obj):
        creator = []
        for c in obj.isadcreator_set.all():
            creator.append(c.creator)
        for i in obj.isaar.all():
            creator.append(i.name)
        return creator

    def get_archival_unit_theme(self, obj):
        return list(map(lambda t: t.theme, obj.archival_unit.theme.all()))

    class Meta:
        model = Isad
        fields = (
            'id', 'ams_id',
            'record_origin', 'record_origin_facet',
            'archival_level', 'archival_level_facet',
            'reference_code', 'reference_code_sort', 'archival_reference_number_search',
            'title', 'title_e', 'title_search', 'title_sort',
            'description_level', 'description_level_facet',
            'date_created', 'date_created_search', 'date_created_facet',
            'fonds', 'fonds_sort', 'subfonds', 'subfonds_sort', 'series', 'series_sort',
            'fonds_name', 'subfonds_name',
            'scope_and_content_abstract_search', 'scope_and_content_narrative_search',
            'archival_history_search', 'publication_note_search',
            'primary_type', 'primary_type_facet',
            'language', 'language_facet',
            'creator', 'creator_facet',
            'archival_unit_theme', 'archival_unit_theme_facet',
        )