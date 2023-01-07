from hashids import Hashids
from rest_framework import serializers

from archival_unit.models import ArchivalUnit


class ArchivalUnitSerializer(serializers.ModelSerializer):
    fonds = serializers.SerializerMethodField()
    subfonds = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()

    def get_fonds(self, obj):
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
        hashids = Hashids(salt="osaarchives", min_length=8)
        catalog_id = hashids.encode(obj.fonds * 1000000 + obj.subfonds * 1000 + obj.series)

        return {
            'number': obj.series,
            'reference_code': obj.reference_code,
            'title': obj.title,
            'catalog_id': catalog_id
        }

    class Meta:
        model = ArchivalUnit
        fields = ['fonds', 'subfonds', 'series']