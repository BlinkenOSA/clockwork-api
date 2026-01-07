"""
Serializer for the archival unit "quick view" tree endpoint.

This serializer provides a lightweight subset of ISAD fields required
to render archival unit previews inside hierarchical tree components.
It avoids heavy aggregations and nested relationships for performance.
"""
from rest_framework import serializers
from isad.models import Isad


class ArchivalUnitsTreeQuickViewSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for fast archival unit tree previews.

    This serializer is optimized for:
        - hierarchical tree navigation
        - quick metadata popups
        - minimal payload size

    It exposes essential ISAD description fields along with
    original-language variants where available.
    """

    title_original = serializers.SerializerMethodField()

    def get_title_original(self, obj):
        """
        Returns the original-language title of the linked archival unit.

        This field is resolved from the ArchivalUnit model rather than
        the ISAD record itself.
        """
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

