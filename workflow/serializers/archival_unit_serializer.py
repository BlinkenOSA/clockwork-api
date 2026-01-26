from hashids import Hashids
from rest_framework import serializers

from archival_unit.models import ArchivalUnit


class ArchivalUnitSerializer(serializers.ModelSerializer):
    """
    Serializer for archival unit identifiers used by workflow endpoints.

    This serializer exposes a compact hierarchical representation of an
    :class:`archival_unit.models.ArchivalUnit` as three nested objects:
        - fonds
        - subfonds
        - series

    Each level includes:
        - numeric identifier (fonds/subfonds/series number)
        - reference code
        - title
        - derived catalog_id (Hashids-based)
    """

    fonds = serializers.SerializerMethodField()
    subfonds = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()

    def get_fonds(self, obj):
        """
        Returns fonds-level metadata for the given archival unit.

        The fonds catalog id is computed from the fonds' hierarchical numbers
        using the same encoding scheme as the public catalog.

        Returns:
            dict: Fonds metadata payload.
        """
        fonds = obj.get_fonds()
        hashids = Hashids(salt="osaarchives", min_length=8)
        catalog_id = hashids.encode(fonds.fonds * 1000000 + fonds.subfonds * 1000 + fonds.series)

        return {
            'number': obj.fonds,
            'reference_code': fonds.reference_code,
            'title': fonds.title,
            'catalog_id': catalog_id
        }

    def get_subfonds(self, obj):
        """
        Returns subfonds-level metadata for the given archival unit.

        The subfonds catalog id is computed from the subfonds' hierarchical numbers
        using the same encoding scheme as the public catalog.

        Returns:
            dict: Subfonds metadata payload.
        """
        subfonds = obj.get_subfonds()
        hashids = Hashids(salt="osaarchives", min_length=8)
        catalog_id = hashids.encode(subfonds.fonds * 1000000 + subfonds.subfonds * 1000 + subfonds.series)

        return {
            'number': obj.subfonds,
            'reference_code': subfonds.reference_code,
            'title': subfonds.title,
            'catalog_id': catalog_id
        }

    def get_series(self, obj):
        """
        Returns series-level metadata for the given archival unit.

        The series catalog id is computed from the current unit's hierarchical numbers
        using the same encoding scheme as the public catalog.

        Returns:
            dict: Series metadata payload.
        """
        hashids = Hashids(salt="osaarchives", min_length=8)
        catalog_id = hashids.encode(obj.fonds * 1000000 + obj.subfonds * 1000 + obj.series)

        return {
            'number': obj.series,
            'reference_code': obj.reference_code,
            'title': obj.title,
            'catalog_id': catalog_id
        }

    class Meta:
        ref_name = 'ArchivalUnitWorkflowSerializer'
        model = ArchivalUnit
        fields = ['fonds', 'subfonds', 'series']
