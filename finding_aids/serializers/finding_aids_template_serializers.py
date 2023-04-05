from drf_writable_nested import WritableNestedModelSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from archival_unit.models import ArchivalUnit
from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from clockwork_api.mixins.user_data_serializer_mixin import UserDataSerializerMixin
from finding_aids.models import FindingAidsEntity
from finding_aids.serializers.finding_aids_entity_serializers import FindingAidsEntityPlaceOfCreationSerializer, \
    FindingAidsEntityCreatorSerializer, FindingAidsEntityDateSerializer, \
    FindingAidsEntityAlternativeTitleSerializer, FindingAidsEntityAssociatedPersonSerializer, \
    FindingAidsEntitySubjectSerializer, FindingAidsEntityAssociatedCorporationSerializer, \
    FindingAidsEntityAssociatedPlaceSerializer, FindingAidsEntityAssociatedCountrySerializer, \
    FindingAidsEntityLanguageSerializer, FindingAidsEntityExtentSerializer


class FindingAidsTemplateListSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'template_name', 'is_removable')


class FindingAidsTemplateWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    archival_unit = serializers.PrimaryKeyRelatedField(queryset=ArchivalUnit.objects.all(), required=False)
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set', required=False)
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set', required=False)
    date_from = ApproximateDateSerializerField(required=False)
    date_to = ApproximateDateSerializerField(required=False)
    dates = FindingAidsEntityDateSerializer(many=True, source='findingaidsentitydate_set', required=False)
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
    languges = FindingAidsEntityLanguageSerializer(many=True, source='findingaidsentitylanguage_set', required=False)
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
