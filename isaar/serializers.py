from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from authority.serializers import LanguageSelectSerializer
from isaar.models import Isaar, IsaarParallelName, IsaarOtherName, IsaarStandardizedName, IsaarCorporateBodyIdentifier, \
    IsaarPlace, IsaarPlaceQualifier


class IsaarOtherNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarOtherName
        exclude = ('isaar',)


class IsaarParallelNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarParallelName
        exclude = ('isaar',)


class IsaarStandardizedNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarStandardizedName
        exclude = ('isaar',)


class IsaarCorporateBodyIdentifierSerizlier(serializers.ModelSerializer):
    class Meta:
        model = IsaarCorporateBodyIdentifier
        exclude = ('isaar',)


class IsaarPlaceQualifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarPlaceQualifier
        exclude = ('isaar',)


class IsaarPlaceReadSerializer(serializers.ModelSerializer):
    place_qualifier = IsaarPlaceQualifierSerializer()

    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarReadSerializer(serializers.ModelSerializer):
    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set')
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set')
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set')
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerizlier(many=True, source='isaarcorporatebodyidentifier_set')
    places = IsaarPlaceReadSerializer(many=True, source='isaarplace_set')
    language = LanguageSelectSerializer(many=True)

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarWriteSerializer(WritableNestedModelSerializer):
    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set')
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set')
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set')
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerizlier(many=True, source='isaarcorporatebodyidentifier_set')
    places = IsaarPlaceSerializer = IsaarPlaceWriteSerializer(many=True, source='isaarplaceserializer_set')

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isaar
        fields = ('id', 'name', 'type', 'status')

