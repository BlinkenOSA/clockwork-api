from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from authority.serializers import LanguageSelectSerializer
from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from controlled_list.serializers import DateTypeSelectSerializer, CorporationRoleSelectSerializer, \
    PersonRoleSelectSerializer, GeoRoleSelectSerializer, LanguageUsageSelectSerializer, ExtentUnitSelectSerializer
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAlternativeTitle, FindingAidsEntityDate, \
    FindingAidsEntityCreator, FindingAidsEntityPlaceOfCreation, FindingAidsEntitySubject, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, FindingAidsEntityAssociatedCountry, \
    FindingAidsEntityAssociatedPlace, FindingAidsEntityLanguage, FindingAidsEntityExtent


class FindingAidsEntityExtentReadSerializer(serializers.ModelSerializer):
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
    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPlaceWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountryReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountryWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPersonReadSerializer(serializers.ModelSerializer):
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
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField()
    date_type = DateTypeSelectSerializer()

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityDateWriteSerializer(serializers.ModelSerializer):
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField()

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityAlternativeTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAlternativeTitle
        exclude = ('fa_entity',)


class FindingAidsEntityListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'title', 'level', 'date_from', 'date_to', 'catalog_id',
                  'published', 'confidential', 'is_removable')


class FindingAidsEntityReadSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set')
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set')
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField()
    dates = FindingAidsEntityDateWriteSerializer(many=True, source='findingaidsentitydate_set')
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set')
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set')
    associated_people = FindingAidsEntityAssociatedPersonReadSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_corporations = FindingAidsEntityAssociatedCorporationReadSerializer(
        many=True, source='findingaidsentityassociatedcorporation_set')
    associated_places = FindingAidsEntityAssociatedPlaceReadSerializer(
        many=True, source='findingaidsentityassociatedplace_set'
    )
    associated_countries = FindingAidsEntityAssociatedCountryReadSerializer(
        many=True, source='findingaidsentityassociatedcountry_set'
    )
    languges = FindingAidsEntityLanguageReadSerializer(many=True, source='findingaidsentitylanguage_set')
    extents = FindingAidsEntityExtentReadSerializer(many=True, source='findingaidsentityextent_set')
    archival_unit_title = serializers.SerializerMethodField()
    container_title = serializers.SerializerMethodField()
    digital_version_exists_container = serializers.SerializerMethodField()

    def get_archival_unit_title(self, obj):
        return obj.archival_unit.title_full

    def get_container_title(self, obj):
        return '%s #%s' % (obj.container.carrier_type.type, obj.container.container_no) if not obj.is_template else ''

    def get_digital_version_exists_container(self, obj):
        if obj.container:
            if obj.container.digital_version_exists:
                return {
                    'digital_version': True,
                    'digital_version_online': obj.container.digital_version_online,
                    'digital_version_barcode': obj.container.barcode
                }
            else:
                return {
                    'digital_version': False
                }
        else:
            return {
                'digital_version': False
            }

    class Meta:
        model = FindingAidsEntity
        fields = '__all__'


class FindingAidsEntityWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all(), required=False)
    archival_unit = serializers.PrimaryKeyRelatedField(queryset=ArchivalUnit.objects.all(), required=False)
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set', required=False)
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set', required=False)
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False)
    dates = FindingAidsEntityDateWriteSerializer(many=True, source='findingaidsentitydate_set', required=False)
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set', required=False)
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set', required=False)
    associated_people = FindingAidsEntityAssociatedPersonWriteSerializer(
        many=True, source='findingaidsentityassociatedperson_set', required=False)
    associated_corporations = FindingAidsEntityAssociatedCorporationWriteSerializer(
        many=True, source='findingaidsentityassociatedcorporation_set', required=False)
    associated_places = FindingAidsEntityAssociatedPlaceWriteSerializer(
        many=True, source='findingaidsentityassociatedplace_set', required=False
    )
    associated_countries = FindingAidsEntityAssociatedCountryWriteSerializer(
        many=True, source='findingaidsentityassociatedcountry_set', required=False
    )
    languges = FindingAidsEntityLanguageWriteSerializer(many=True, source='findingaidsentitylanguage_set', required=False)
    extents = FindingAidsEntityExtentWriteSerializer(many=True, source='findingaidsentityextent_set', required=False)

    def validate(self, data):
        date_from = data.get('date_from', None)
        date_to = data.get('date_to', None)
        if date_to:
            if date_from > date_to:
                raise ValidationError("Date from value is bigger than date to value.")
        return data

    class Meta:
        model = FindingAidsEntity
        fields = '__all__'


class FindingAidsSelectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'title', 'archival_reference_code', 'description_level', 'level', 'contents_summary')
