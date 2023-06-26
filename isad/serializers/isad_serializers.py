from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from clockwork_api.mixins.isad_archival_unit_serializer_mixin import IsadArchivalUnitSerializerMixin
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import CarrierTypeSelectSerializer, ExtentUnitSelectSerializer
from isad.models import Isad, IsadCreator, IsadCarrier, IsadExtent, IsadLocationOfOriginals, IsadLocationOfCopies, \
    IsadRelatedFindingAids


class IsadCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCreator
        exclude = ('isad',)


class IsadCarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCarrier
        exclude = ('isad',)


class IsadExtentSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadExtent
        exclude = ('isad',)


class IsadLocationOfOriginalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfOriginals
        exclude = ('isad',)


class IsadLocationOfCopiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfCopies
        exclude = ('isad',)


class IsadRelatedFindingAidsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadRelatedFindingAids
        exclude = ('isad',)


class IsadReadSerializer(serializers.ModelSerializer):
    creators = IsadCreatorSerializer(many=True, source='isadcreator_set')
    carriers = IsadCarrierSerializer(many=True, source='isadcarrier_set')
    extents = IsadExtentSerializer(many=True, source='isadextent_set')
    related_finding_aids = IsadRelatedFindingAidsSerializer(many=True, source='isadrelatedfindingaids_set')
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set')
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set')
    title_full = serializers.SerializerMethodField()

    def get_title_full(self, obj):
        return obj.archival_unit.title_full

    class Meta:
        model = Isad
        fields = '__all__'


class IsadWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    creators = IsadCreatorSerializer(many=True, source='isadcreator_set', required=False)
    carriers = IsadCarrierSerializer(many=True, source='isadcarrier_set', required=False)
    extents = IsadExtentSerializer(many=True, source='isadextent_set', required=False)
    related_finding_aids = IsadRelatedFindingAidsSerializer(many=True, source='isadrelatedfindingaids_set', required=False)
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set', required=False)
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set', required=False)

    class Meta:
        model = Isad
        fields = '__all__'


class IsadSeriesSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'reference_code', 'title', 'status')


class IsadSubfondsSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_children(self, obj):
        user = self.context['user']
        if user.user_profile.allowed_archival_units.count() > 0:
            queryset = ArchivalUnit.objects.none()
            for archival_unit in user.user_profile.allowed_archival_units.filter(
                fonds=obj.fonds, subfonds=obj.subfonds
            ):
                queryset |= ArchivalUnit.objects.filter(
                    fonds=archival_unit.fonds,
                    subfonds=archival_unit.subfonds,
                    series=archival_unit.series,
                    level='S')
            return IsadSeriesSerializer(queryset, many=True, context=self.context).data
        else:
            if obj.children.count() > 0:
                return IsadSeriesSerializer(obj.children, many=True, context=self.context).data
            else:
                return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'status')


class IsadFondsSerializer(IsadArchivalUnitSerializerMixin, serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    def get_children(self, obj):
        user = self.context['user']
        if user.user_profile.allowed_archival_units.count() > 0:
            queryset = ArchivalUnit.objects.none()
            for archival_unit in user.user_profile.allowed_archival_units.filter(fonds=obj.fonds):
                queryset |= ArchivalUnit.objects.filter(
                    fonds=archival_unit.fonds,
                    subfonds=archival_unit.subfonds,
                    level='SF')
            return IsadSubfondsSerializer(queryset, many=True, context=self.context).data
        else:
            if obj.children.count() > 0:
                return IsadSubfondsSerializer(obj.children, many=True, context=self.context).data
            else:
                return None

    class Meta:
        model = ArchivalUnit
        fields = ('id', 'isad', 'fonds', 'subfonds', 'series', 'level', 'children', 'reference_code', 'title', 'status')


class IsadPreCreateSerializer(serializers.ModelSerializer):
    archival_unit = serializers.SerializerMethodField()
    description_level = serializers.CharField(source='level')

    def get_archival_unit(self, obj):
        return obj.id

    class Meta:
        model = ArchivalUnit
        fields = ('archival_unit', 'reference_code', 'title', 'description_level')


class IsadSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isad
        fields = ('id', 'reference_code', 'title', 'published')
