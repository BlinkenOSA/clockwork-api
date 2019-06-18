from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from archival_unit.serializers import ArchivalUnitSelectSerializer
from authority.serializers import LanguageSelectSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import AccessRightSelectSerializer, ReproductionRightSelectSerializer, \
    LocaleSelectSerializer, RightsRestrictionReasonSelectSerializer, CarrierTypeSelectSerializer, \
    ExtentUnitSelectSerializer
from isaar.serializers import IsaarSelectSerializer
from isad.models import Isad, IsadCreator, IsadCarrier, IsadExtent, IsadLocationOfOriginals, IsadLocationOfCopies


class IsadCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCreator
        fields = '__all__'


class IsadCarrierReadSerializer(serializers.ModelSerializer):
    carrier_type = CarrierTypeSelectSerializer()

    class Meta:
        model = IsadCarrier
        fields = '__all__'


class IsadCarrierWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCarrier
        fields = '__all__'


class IsadExtentReadSerializer(serializers.ModelSerializer):
    extent_unit = ExtentUnitSelectSerializer()

    class Meta:
        model = IsadExtent
        fields = '__all__'


class IsadExtentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadExtent
        fields = '__all__'


class IsadLocationOfOriginalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfOriginals
        fields = '__all__'


class IsadLocationOfCopiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfCopies
        fields = '__all__'


class IsadReadSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSelectSerializer()
    original_locale = LocaleSelectSerializer()
    isaar = IsaarSelectSerializer(many=True)
    language = LanguageSelectSerializer(many=True)
    access_rights = AccessRightSelectSerializer()
    reproduction_rights = ReproductionRightSelectSerializer()
    rights_restriction_reason = RightsRestrictionReasonSelectSerializer()

    creators = IsadCreatorSerializer(many=True, source='isadcreator_set')
    carriers = IsadCarrierReadSerializer(many=True, source='isadcarrier_set')
    extents = IsadExtentReadSerializer(many=True, source='isadextent_set')
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set')
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set')

    class Meta:
        model = Isad
        fields = '__all__'


class IsadWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    title = serializers.CharField(required=False)
    reference_code = serializers.CharField(required=False)
    creators = IsadCreatorSerializer(many=True, source='isadcreator_set')
    carriers = IsadCarrierWriteSerializer(many=True, source='isadcarrier_set')
    extents = IsadExtentWriteSerializer(many=True, source='isadextent_set')
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set')
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set')

    class Meta:
        model = Isad
        fields = '__all__'


class IsadSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isad
        fields = ('id', 'reference_code', 'title', 'published')