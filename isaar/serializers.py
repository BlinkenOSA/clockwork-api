from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from clockwork_api.fields import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from isaar.models import Isaar, IsaarParallelName, IsaarOtherName, IsaarStandardizedName, IsaarCorporateBodyIdentifier, \
    IsaarPlace, IsaarPlaceQualifier, IsaarRelationship


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
        fields = '__all__'


class IsaarPlaceReadSerializer(serializers.ModelSerializer):
    place_qualifier = IsaarPlaceQualifierSerializer()

    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarPlace
        exclude = ('isaar',)


class IsaarListSerializer(serializers.ModelSerializer):
    isad = serializers.SlugRelatedField(many=True, slug_field='reference_code', read_only=True, source='isad_set')

    class Meta:
        model = Isaar
        fields = ['id', 'name', 'type', 'status', 'isad']


class IsaarReadSerializer(serializers.ModelSerializer):
    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set')
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set')
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set')
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerizlier(many=True, source='isaarcorporatebodyidentifier_set')
    places = IsaarPlaceReadSerializer(many=True, source='isaarplace_set')

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    date_existence_from = ApproximateDateSerializerField()
    date_existence_to = ApproximateDateSerializerField()
    parallel_names = IsaarParallelNameSerializer(many=True, source='isaarparallelname_set')
    other_names = IsaarOtherNameSerializer(many=True, source='isaarothername_set')
    standardized_names = IsaarStandardizedNameSerializer(many=True, source='isaarstandardizedname_set')
    corporate_body_identifiers = IsaarCorporateBodyIdentifierSerizlier(many=True, source='isaarcorporatebodyidentifier_set')
    places = IsaarPlaceWriteSerializer(many=True, source='isaarplace_set')

    class Meta:
        model = Isaar
        fields = '__all__'


class IsaarSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Isaar
        fields = ('id', 'name', 'type', 'status')


class IsaarRelationshipSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsaarRelationship
        fields = ('id', 'relationship')
