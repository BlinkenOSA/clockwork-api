from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from container.models import Container
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAlternativeTitle, FindingAidsEntityDate, \
    FindingAidsEntityCreator, FindingAidsEntityPlaceOfCreation, FindingAidsEntitySubject, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, FindingAidsEntityAssociatedCountry, \
    FindingAidsEntityAssociatedPlace, FindingAidsEntityLanguage, FindingAidsEntityExtent, FindingAidsEntityIdentifier


class FindingAidsEntityExtentSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityExtent
        exclude = ('fa_entity',)


class FindingAidsEntityLanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityLanguage
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPersonSerializer(serializers.ModelSerializer):
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


class FindingAidsEntityDateSerializer(serializers.ModelSerializer):
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False, default='')

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityIdentifierSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityIdentifier
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
    dates = FindingAidsEntityDateSerializer(many=True, source='findingaidsentitydate_set')
    identifiers = FindingAidsEntityIdentifierSerializer(many=True, source='findingaidsentityidentifier_set')
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set')
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set')
    associated_people = FindingAidsEntityAssociatedPersonSerializer(
        many=True, source='findingaidsentityassociatedperson_set')
    associated_corporations = FindingAidsEntityAssociatedCorporationSerializer(
        many=True, source='findingaidsentityassociatedcorporation_set')
    associated_places = FindingAidsEntityAssociatedPlaceSerializer(
        many=True, source='findingaidsentityassociatedplace_set'
    )
    associated_countries = FindingAidsEntityAssociatedCountrySerializer(
        many=True, source='findingaidsentityassociatedcountry_set'
    )
    languages = FindingAidsEntityLanguageSerializer(many=True, source='findingaidsentitylanguage_set')
    extents = FindingAidsEntityExtentSerializer(many=True, source='findingaidsentityextent_set')
    archival_unit_title = serializers.SerializerMethodField()
    container_title = serializers.SerializerMethodField()
    digital_version_exists_container = serializers.SerializerMethodField()

    def get_archival_unit_title(self, obj):
        return obj.archival_unit.title_full

    def get_container_title(self, obj):
        return '%s #%s' % (obj.container.carrier_type.type, obj.container.container_no) if not obj.is_template else ''

    def get_digital_version_exists_container(self, obj):
        if obj.container:
            return {
                'digital_version': obj.container.digital_version_exists,
                'digital_version_online': obj.container.digital_version_online,
                'digital_version_research_cloud': obj.container.digital_version_research_cloud,
                'digital_version_research_cloud_path': obj.container.digital_version_research_cloud_path,
                'digital_version_barcode': obj.container.barcode
            }
        else:
            return {
                'digital_version': False
            }

    class Meta:
        model = FindingAidsEntity
        exclude = ('duration',)


class FindingAidsEntityWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all(), required=False)
    archival_unit = serializers.PrimaryKeyRelatedField(queryset=ArchivalUnit.objects.all(), required=False)
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set', required=False)
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set', required=False)
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False)
    dates = FindingAidsEntityDateSerializer(many=True, source='findingaidsentitydate_set', required=False)
    identifiers = FindingAidsEntityIdentifierSerializer(
        many=True, source='findingaidsentityidentifier_set', required=False)
    alternative_titles = FindingAidsEntityAlternativeTitleSerializer(
        many=True, source='findingaidsentityalternativetitle_set', required=False)
    subjects = FindingAidsEntitySubjectSerializer(many=True, source='findingaidsentitysubject_set', required=False)
    associated_people = FindingAidsEntityAssociatedPersonSerializer(
        many=True, source='findingaidsentityassociatedperson_set', required=False)
    associated_corporations = FindingAidsEntityAssociatedCorporationSerializer(
        many=True, source='findingaidsentityassociatedcorporation_set', required=False)
    associated_places = FindingAidsEntityAssociatedPlaceSerializer(
        many=True, source='findingaidsentityassociatedplace_set', required=False
    )
    associated_countries = FindingAidsEntityAssociatedCountrySerializer(
        many=True, source='findingaidsentityassociatedcountry_set', required=False
    )
    languages = FindingAidsEntityLanguageSerializer(many=True, source='findingaidsentitylanguage_set', required=False)
    extents = FindingAidsEntityExtentSerializer(many=True, source='findingaidsentityextent_set', required=False)

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
