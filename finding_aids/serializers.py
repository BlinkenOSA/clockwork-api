from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers

from authority.serializers import LanguageSelectSerializer
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from controlled_list.serializers import DateTypeSelectSerializer, CorporationRoleSelectSerializer, \
    PersonRoleSelectSerializer, GeoRoleSelectSerializer, LanguageUsageSelectSerializer, ExtentUnitSelectSerializer
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAlternativeTitle, FindingAidsEntityDate, \
    FindingAidsEntityCreator, FindingAidsEntityPlaceOfCreation, FindingAidsEntitySubject, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, FindingAidsEntityAssociatedCountry, \
    FindingAidsEntityAssociatedPlace, FindingAidsEntityLanguage, FindingAidsEntityExtent


class FindingAidsEntityExtentReadSerializer(serializers.ModelSerializer):
    extent_unit = ExtentUnitSelectSerializer()

    class Meta:
        model = FindingAidsEntityExtent
        exclude = ('fa_entity',)


class FindingAidsEntityExtentWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityExtent
        exclude = ('fa_entity',)


class FindingAidsEntityLanguageReadSerializer(serializers.ModelSerializer):
    language = LanguageSelectSerializer()
    language_usage = LanguageUsageSelectSerializer()

    class Meta:
        model = FindingAidsEntityLanguage
        exclude = ('fa_entity',)


class FindingAidsEntityLanguageWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityLanguage
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPlaceReadSerializer(serializers.ModelSerializer):
    role = GeoRoleSelectSerializer()

    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountryReadSerializer(serializers.ModelSerializer):
    role = GeoRoleSelectSerializer()

    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationReadSerializer(serializers.ModelSerializer):
    role = CorporationRoleSelectSerializer()

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPersonReadSerializer(serializers.ModelSerializer):
    role = PersonRoleSelectSerializer()

    class Meta:
        model = FindingAidsEntityAssociatedPerson
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPersonWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedPerson
        exclude = ('fa_entity',)


class FindingAidsEntitySubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntitySubject
        exclude = ('fa_entity',)


class FindingAidsEntityPlaceOfCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityPlaceOfCreation
        exclude = ('fa_entity',)


class FindingAidsEntityCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityCreator
        exclude = ('fa_entity',)


class FindingAidsEntityDateReadSerializer(serializers.ModelSerializer):
    date_type = DateTypeSelectSerializer()

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityDateWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityAlternativeTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAlternativeTitle
        exclude = ('fa_entity',)


class FindingAidsEntityReadSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set')
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set')
    dates = FindingAidsEntityDateWriteSerializer(many=True, source='findingaidsentitydate_set')
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set')
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set')
    associated_people = FindingAidsEntityAssociatedPersonReadSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_corporations = FindingAidsEntityAssociatedCorporationReadSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_places = FindingAidsEntityAssociatedPlaceReadSerializer(
        many=True, source='findingaidsentityassociatedplace_set'
    )
    associated_countries = FindingAidsEntityAssociatedCountryReadSerializer(
        many=True, source='findingaidsentityassociatedcountry_set'
    )
    languges = FindingAidsEntityLanguageReadSerializer(many=True, source='findingaidsentitylanguage_set')
    extents = FindingAidsEntityExtentReadSerializer(many=True, source='findingaidsentityextent_set')

    class Meta:
        model = FindingAidsEntity
        fields = '__all__'


class FindingAidsEntityWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set')
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set')
    dates = FindingAidsEntityDateWriteSerializer(many=True, source='findingaidsentitydate_set')
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set')
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set')
    associated_people = FindingAidsEntityAssociatedPersonWriteSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_corporations = FindingAidsEntityAssociatedCorporationWriteSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_places = FindingAidsEntityAssociatedPlaceWriteSerializer(
        many=True, source='findingaidsentityassociatedplace_set'
    )
    associated_countries = FindingAidsEntityAssociatedCountryWriteSerializer(
        many=True, source='findingaidsentityassociatedcountry_set'
    )
    languges = FindingAidsEntityLanguageWriteSerializer(many=True, source='findingaidsentitylanguage_set')
    extents = FindingAidsEntityExtentWriteSerializer(many=True, source='findingaidsentityextent_set')

    class Meta:
        model = FindingAidsEntity
        exclude = '__all__'


class FindingAidsSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'title', 'archival_reference_code', 'description_level', 'level', 'contents_summary')