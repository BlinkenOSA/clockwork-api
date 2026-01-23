from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from controlled_list.models import CarrierType
from mlr.models import MLREntity, MLREntityLocation


class MLRListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing Master Location Register (MLR) entries.

    This serializer is optimized for list/table views and exposes:
        - the series reference code (slug field)
        - a computed container quantity for the series/carrier type pair
        - the carrier type label (slug field)
        - a computed linear-meter size estimate
        - a computed human-readable MRSS location string

    Notes
    -----
    The computed fields delegate to :class:`mlr.models.MLREntity` helper methods:
        - ``quantity`` -> :meth:`mlr.models.MLREntity.get_count`
        - ``size`` -> :meth:`mlr.models.MLREntity.get_size`
        - ``mrss`` -> :meth:`mlr.models.MLREntity.get_locations`
    """

    series = serializers.SlugRelatedField(slug_field='reference_code', queryset=ArchivalUnit.objects.all())
    quantity = serializers.SerializerMethodField()
    carrier_type = serializers.SlugRelatedField(slug_field='type', queryset=CarrierType.objects.all())
    size = serializers.SerializerMethodField()
    mrss = serializers.SerializerMethodField()

    def get_quantity(self, obj):
        """
        Returns the number of matching containers for this MLR entry.
        """
        return obj.get_count()

    def get_size(self, obj):
        """
        Returns the estimated size (linear meters) for this MLR entry.
        """
        return obj.get_size()

    def get_mrss(self, obj):
        """
        Returns the formatted MRSS location string for this MLR entry.
        """
        return obj.get_locations()

    class Meta:
        model = MLREntity
        fields = ['id', 'series', 'quantity', 'carrier_type', 'size', 'mrss']


class MLREntityLocationsSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`mlr.models.MLREntityLocation`.

    Represents a single location address (building + optional shelf coordinates)
    associated with an MLR entry.
    """

    class Meta:
        model = MLREntityLocation
        fields = ['id', 'building', 'module', 'row', 'section', 'shelf']


class MLREntitySerializer(WritableNestedModelSerializer):
    """
    Read/write serializer for a full Master Location Register (MLR) entry.

    Supports writable nested create/update of associated locations via
    :class:`drf_writable_nested.WritableNestedModelSerializer`.

    Exposes:
        - the series foreign key
        - a derived series display name (``series_name``)
        - the carrier type foreign key
        - nested ``locations``
        - optional free-text ``notes``
    """

    series_name = serializers.SerializerMethodField()
    locations = MLREntityLocationsSerializer(many=True)

    def get_series_name(self, obj):
        """
        Returns the full series title for display purposes.
        """
        return obj.series.title_full

    class Meta:
        model = MLREntity
        fields = ['id', 'series', 'series_name', 'carrier_type', 'locations', 'notes']
