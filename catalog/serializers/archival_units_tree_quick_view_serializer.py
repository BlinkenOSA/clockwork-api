from rest_framework import serializers
from isad.models import Isad


class ArchivalUnitsTreeQuickViewSerializer(serializers.ModelSerializer):
    title_original = serializers.SerializerMethodField()

    def get_title_original(self, obj):
        return obj.archival_unit.title_original

    class Meta:
        model = Isad
        fields = ['id', 'reference_code', 'original_locale', 'catalog_id',
                  'year_from', 'year_to', 'date_predominant',
                  'title', 'title_original',
                  'description_level',
                  'archival_history', 'archival_history_original',
                  'scope_and_content_abstract', 'scope_and_content_abstract_original',
                  'scope_and_content_narrative', 'scope_and_content_narrative_original']

