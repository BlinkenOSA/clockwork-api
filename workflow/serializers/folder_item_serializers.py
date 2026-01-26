from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from finding_aids.models import FindingAidsEntity


class ArchivalUnitSerializer(serializers.ModelSerializer):
    """
    Serializer for archival unit metadata in workflow digitization endpoints.

    Provides a full representation of an archival unit, including:
        - hierarchical level (fonds, subfonds, series)
        - assigned thematic categories
        - descriptive and reference metadata

    Used primarily for workflow and preservation-related API responses.
    """

    theme = serializers.StringRelatedField(many=True)
    level = serializers.SerializerMethodField()

    def get_level(self, obj):
        """
        Returns the human-readable description level.

        Args:
            obj: ArchivalUnit instance.

        Returns:
            str: One of "Fonds", "Subfonds", or "Series".
        """
        if obj.level == 'F':
            return 'Fonds'
        elif obj.level == 'SF':
            return 'Subfonds'
        else:
            return 'Series'

    class Meta:
        model = ArchivalUnit
        fields = '__all__'


class FADigitizedSerializer(serializers.ModelSerializer):
    """
    Serializer for digitized finding aids records.

    Exposes descriptive and hierarchical metadata for digitized
    finding aids entities, including their parent archival unit.

    Used by workflow services for:
        - validating digitization outputs
        - synchronizing metadata
        - publishing digitized finding aids
    """

    archival_unit = ArchivalUnitSerializer(read_only=True)

    class Meta:
        model = FindingAidsEntity
        fields = [
            'archival_unit',
            'title',
            'folder_no',
            'sequence_no',
            'catalog_id',
            'archival_reference_code',
        ]
