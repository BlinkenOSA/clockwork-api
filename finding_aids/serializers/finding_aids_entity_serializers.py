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
    FindingAidsEntityAssociatedPlace, FindingAidsEntityLanguage, FindingAidsEntityExtent, FindingAidsEntityIdentifier, \
    FindingAidsEntityRelatedMaterial


class FindingAidsEntityExtentSerializer(serializers.ModelSerializer):
    """
    Nested serializer for extent entries.

    Used as a writable nested component of FindingAidsEntity read/write serializers.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityExtent
        exclude = ('fa_entity',)


class FindingAidsEntityLanguageSerializer(serializers.ModelSerializer):
    """
    Nested serializer for language entries.

    Used as a writable nested component of FindingAidsEntity read/write serializers.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityLanguage
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPlaceSerializer(serializers.ModelSerializer):
    """
    Nested serializer for associated place relations.

    Links a finding aids entity to an authority place record and optional geo role.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCountrySerializer(serializers.ModelSerializer):
    """
    Nested serializer for associated country relations.

    Links a finding aids entity to an authority country record and optional geo role.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedCorporationSerializer(serializers.ModelSerializer):
    """
    Nested serializer for associated corporation relations.

    Links a finding aids entity to an authority corporation record and optional role.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('fa_entity',)


class FindingAidsEntityAssociatedPersonSerializer(serializers.ModelSerializer):
    """
    Nested serializer for associated person relations.

    Links a finding aids entity to an authority person record and optional role.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityAssociatedPerson
        exclude = ('fa_entity',)


class FindingAidsEntitySubjectSerializer(serializers.ModelSerializer):
    """
    Nested serializer for free-text subject entries.

    Supports literal subject strings when authority subjects are not used.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntitySubject
        exclude = ('fa_entity',)


class FindingAidsEntityPlaceOfCreationSerializer(serializers.ModelSerializer):
    """
    Nested serializer for free-text place of creation entries.

    Stores literal place strings (not authority Place records).
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityPlaceOfCreation
        exclude = ('fa_entity',)


class FindingAidsEntityCreatorSerializer(serializers.ModelSerializer):
    """
    Nested serializer for creator entries.

    Creators are stored as free-text values with a controlled role label.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityCreator
        exclude = ('fa_entity',)


class FindingAidsEntityDateSerializer(serializers.ModelSerializer):
    """
    Nested serializer for typed date ranges.

    Uses ApproximateDateSerializerField to support imprecise dates.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False, default='')

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('fa_entity',)


class FindingAidsEntityIdentifierSerializer(serializers.ModelSerializer):
    """
    Nested serializer for typed identifier entries.

    Identifiers store a value plus a controlled IdentifierType.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityIdentifier
        exclude = ('fa_entity',)


class FindingAidsEntityAlternativeTitleSerializer(serializers.ModelSerializer):
    """
    Nested serializer for alternative title entries.

    Alternative titles support variants/translations separate from the main title.
    The parent link (fa_entity) is excluded and managed by the nested write framework.
    """

    class Meta:
        model = FindingAidsEntityAlternativeTitle
        exclude = ('fa_entity',)


class FindingAidsEntityListSerializer(serializers.ModelSerializer):
    """
    Compact serializer for listing finding aids entities.

    Intended for list views where only identification and core display fields
    are needed, plus published/confidential/removability flags for UI behavior.
    """

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'archival_reference_code', 'title', 'level', 'date_from', 'date_to', 'catalog_id',
                  'published', 'confidential', 'is_removable')


class FindingAidsEntityRelatedMaterialSerializer(serializers.ModelSerializer):
    """
    Nested serializer for related material relationships.

    Used as a nested component on the relationship_sources side. The `source`
    field is excluded because it is the parent entity in the nested context.
    """

    class Meta:
        model = FindingAidsEntityRelatedMaterial
        exclude = ('source',)


class FindingAidsEntityReadSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Full read serializer for a finding aids entity.

    Provides:
        - complete entity field output (fields='__all__')
        - nested representations for related tables (dates, creators, subjects, etc.)
        - computed display/context fields (archival_unit_title, container_title)
        - container-level digital version summary for UI (digital_version_exists_container)

    Note:
        Nested relations are exposed via their reverse relation sets using `source=..._set`.
        This serializer is read-oriented but still uses WritableNestedModelSerializer for
        consistent structure with the write serializer.
    """

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
    related_materials = FindingAidsEntityRelatedMaterialSerializer(
        many=True, source='relationship_sources'
    )
    archival_unit_title = serializers.SerializerMethodField()
    container_title = serializers.SerializerMethodField()
    digital_version_exists_container = serializers.SerializerMethodField()

    def get_archival_unit_title(self, obj):
        """
        Returns the archival unit display title for UI use.
        """
        return obj.archival_unit.title_full

    def get_container_title(self, obj):
        """
        Returns a human-readable container label for UI use.

        For templates, containers are not applicable and an empty string is returned.
        """
        return '%s #%s' % (obj.container.carrier_type.type, obj.container.container_no) if not obj.is_template else ''

    def get_digital_version_exists_container(self, obj):
        """
        Returns a summary of container-level digitization flags.

        This is used by clients to show container digitization state alongside
        the entity-level state.
        """
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
        fields = '__all__'


class FindingAidsEntityWriteSerializer(UserDataSerializerMixin, WritableNestedModelSerializer):
    """
    Full write serializer for a finding aids entity.

    Supports writable nested updates via drf-writable-nested for:
        - dates, creators, identifiers, subjects, extents, languages, related materials, etc.

    Validation:
        - enforces that date_from is not later than date_to when date_to is present

    Notes:
        - container and archival_unit are PK fields to simplify write operations
        - duration is excluded because it is computed on the model
    """

    container = serializers.PrimaryKeyRelatedField(queryset=Container.objects.all(), required=False)
    archival_unit = serializers.PrimaryKeyRelatedField(queryset=ArchivalUnit.objects.all(), required=False)
    places_of_creation = FindingAidsEntityPlaceOfCreationSerializer(
        many=True, source='findingaidsentityplaceofcreation_set', required=False)
    creators = FindingAidsEntityCreatorSerializer(many=True, source='findingaidsentitycreator_set', required=False)
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False)
    date_ca_span = serializers.IntegerField(required=False, default=0)
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
    related_materials = FindingAidsEntityRelatedMaterialSerializer(
        many=True, source='relationship_sources', required=False
    )

    def validate(self, data):
        """
        Validates date range consistency.

        Ensures date_from is not greater than date_to when date_to is provided.
        """
        date_from = data.get('date_from', None)
        date_to = data.get('date_to', None)
        if date_to:
            if date_from > date_to:
                raise ValidationError("Date from value is bigger than date to value.")
        return data

    class Meta:
        model = FindingAidsEntity
        exclude = ('duration',)


class FindingAidsSelectSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for selection/autocomplete use cases.

    Intended for UI components that need basic identification and a preview
    of the record, without nested data.
    """

    class Meta:
        model = FindingAidsEntity
        fields = ('id', 'title', 'archival_reference_code', 'description_level', 'level', 'contents_summary')
