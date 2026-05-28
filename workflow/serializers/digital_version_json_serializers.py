from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from authority.models import Language, Place, Country, Person, Corporation, Genre, Subject
from clockwork_api.fields.approximate_date_serializer_field import ApproximateDateSerializerField
from container.models import Container
from controlled_list.models import AccessRight, ReproductionRight, ExtentUnit, DateType, LanguageUsage, GeoRole, \
    CorporationRole, PersonRole, IdentifierType, PrimaryType, Keyword
from finding_aids.models import FindingAidsEntity, FindingAidsEntityDate, FindingAidsEntityRelatedMaterial, \
    FindingAidsEntityIdentifier, FindingAidsEntityAlternativeTitle, FindingAidsEntityExtent, FindingAidsEntityLanguage, \
    FindingAidsEntityAssociatedPlace, FindingAidsEntityAssociatedCountry, FindingAidsEntityAssociatedCorporation, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntitySubject, FindingAidsEntityCreator, \
    FindingAidsEntityPlaceOfCreation
from isaar.models import Isaar
from isad.models import IsadCreator, IsadCarrier, IsadExtent, IsadLocationOfOriginals, IsadLocationOfCopies, \
    IsadRelatedFindingAids, Isad


class PersonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Person
        fields = ('first_name', 'last_name', 'wikidata_id', 'wiki_url', 'authority_url')


class CorporationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corporation
        fields = ('name', 'wikidata_id', 'wiki_url', 'authority_url')


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ('country', 'alpha2', 'alpha3', 'wikidata_id', 'wiki_url', 'authority_url')


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ('place', 'wikidata_id', 'wiki_url', 'authority_url')


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('genre', 'wikidata_id', 'wiki_url', 'authority_url')


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = ('language', 'iso_639_1', 'iso_639_2', 'wikidata_id', 'wiki_url', 'authority_url')


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ('subject', 'wikidata_id', 'wiki_url', 'authority_url')


class KeywordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Keyword
        fields = ('keyword',)

class IsadCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCreator
        exclude = ('id', 'isad',)


class IsadCarrierSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadCarrier
        exclude = ('id', 'isad',)


class IsadExtentSerializer(serializers.ModelSerializer):
    extent_unit = serializers.SlugRelatedField('unit', queryset=ExtentUnit.objects.all())

    class Meta:
        model = IsadExtent
        exclude = ('id', 'isad',)


class IsadLocationOfOriginalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfOriginals
        exclude = ('id', 'isad',)


class IsadLocationOfCopiesSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadLocationOfCopies
        exclude = ('id', 'isad',)


class IsadRelatedFindingAidsSerializer(serializers.ModelSerializer):
    class Meta:
        model = IsadRelatedFindingAids
        exclude = ('id', 'isad',)


class WorkflowIsadSerializer(serializers.ModelSerializer):
    creators = IsadCreatorSerializer(many=True, source='isadcreator_set')
    carriers = IsadCarrierSerializer(many=True, source='isadcarrier_set')
    extents = IsadExtentSerializer(many=True, source='isadextent_set')
    related_finding_aids = IsadRelatedFindingAidsSerializer(many=True, source='isadrelatedfindingaids_set')
    location_of_originals = IsadLocationOfOriginalsSerializer(many=True, source='isadlocationoforiginals_set')
    location_of_copies = IsadLocationOfCopiesSerializer(many=True, source='isadlocationofcopies_set')
    title_full = serializers.SerializerMethodField()
    isaar = serializers.SlugRelatedField(slug_field='name', queryset=Isaar.objects.all())
    reproduction_rights = serializers.SlugRelatedField(slug_field='statement', queryset=ReproductionRight.objects.all())
    language = LanguageSerializer(read_only=True, many=True)

    def get_title_full(self, obj):
        """
        Returns the full archival unit title for display purposes.
        """
        return obj.archival_unit.title_full

    class Meta:
        model = Isad
        exclude = [
            'id', 'published', 'user_published', 'date_published', 'user_created', 'date_created',
            'user_updated', 'date_updated', 'archival_unit', 'access_rights_legacy', 'access_rights_legacy_original',
            'reproduction_rights_legacy', 'reproduction_rights_legacy_original', 'access_rights'
        ]


class WorkflowArchivalUnitSerializer(serializers.ModelSerializer):
    isad = serializers.SerializerMethodField()

    def get_isad(self, obj):
        if hasattr(obj, 'isad'):
            return WorkflowIsadSerializer(obj.isad).data
        return None

    class Meta:
        ref_name = 'WorkflowArchivalUnitJSONSerializer'
        model = ArchivalUnit
        fields = ['title', 'title_original', 'reference_code', 'isad']


class WorkflowContainerSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SerializerMethodField()

    def get_carrier_type(self, obj):
        return obj.carrier_type.type if obj.carrier_type else None

    class Meta:
        ref_name = 'WorkflowContainerJSONSerializer'
        model = Container
        fields = ['container_no', 'carrier_type', 'legacy_id', 'barcode']


class FindingAidsEntityExtentSerializer(serializers.ModelSerializer):
    extent_unit = serializers.SlugRelatedField('unit', queryset=ExtentUnit.objects.all())

    class Meta:
        model = FindingAidsEntityExtent
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityLanguageSerializer(serializers.ModelSerializer):
    language = LanguageSerializer()
    language_usage = serializers.SlugRelatedField('usage', queryset=LanguageUsage.objects.all())

    class Meta:
        model = FindingAidsEntityLanguage
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityAssociatedPlaceSerializer(serializers.ModelSerializer):
    associated_place = PlaceSerializer()
    role = serializers.SlugRelatedField('role', queryset=GeoRole.objects.all())

    class Meta:
        model = FindingAidsEntityAssociatedPlace
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityAssociatedCountrySerializer(serializers.ModelSerializer):
    associated_country = CountrySerializer()
    role = serializers.SlugRelatedField('role', queryset=GeoRole.objects.all())

    class Meta:
        model = FindingAidsEntityAssociatedCountry
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityAssociatedCorporationSerializer(serializers.ModelSerializer):
    associated_corporation = CorporationSerializer()
    role = serializers.SlugRelatedField('role', queryset=CorporationRole.objects.all())

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityAssociatedPersonSerializer(serializers.ModelSerializer):
    associated_person = PersonSerializer()
    role = serializers.SlugRelatedField('role', queryset=PersonRole.objects.all())

    class Meta:
        model = FindingAidsEntityAssociatedPerson
        exclude = ('id', 'fa_entity',)


class FindingAidsEntitySubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntitySubject
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityPlaceOfCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityPlaceOfCreation
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityCreatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityCreator
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityIdentifierSerializer(serializers.ModelSerializer):
    identifier_type = serializers.SlugRelatedField('type', queryset=IdentifierType.objects.all())

    class Meta:
        model = FindingAidsEntityIdentifier
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityAlternativeTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAlternativeTitle
        exclude = ('id', 'fa_entity',)


class FindingAidsEntityDateSerializer(serializers.ModelSerializer):
    date_from = ApproximateDateSerializerField()
    date_to = ApproximateDateSerializerField(required=False, default='')
    date_type = serializers.SlugRelatedField('type', queryset=DateType.objects.all())

    class Meta:
        model = FindingAidsEntityDate
        exclude = ('id', 'fa_entity',)


class WorkflowFindingAidsEntitySerializer(serializers.ModelSerializer):
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

    spatial_coverage_country = CountrySerializer(many=True, read_only=True)
    spatial_coverage_place = PlaceSerializer(many=True, read_only=True)
    subject_person = PersonSerializer(many=True, read_only=True)
    subject_corporation = CorporationSerializer(many=True, read_only=True)
    subject_heading = SubjectSerializer(many=True, read_only=True)
    subject_keyword = KeywordSerializer(many=True, read_only=True)

    primary_type = serializers.SlugRelatedField('type', queryset=PrimaryType.objects.all())
    genre = GenreSerializer(many=True, read_only=True)
    access_rights = serializers.SlugRelatedField('statement', queryset=AccessRight.objects.all())

    class Meta:
        model = FindingAidsEntity
        exclude = [
            'id', 'published', 'digital_version_exists', 'digital_version_creation_date',
            'digital_version_technical_metadata', 'digital_version_research_cloud',
            'digital_version_research_cloud_path', 'digital_version_online', 'user_published', 'date_published',
            'user_updated', 'date_updated', 'user_created', 'date_created', 'archival_unit', 'container', 'old_id',
            'is_template'
        ]


class DigitalObjectJSONSerializer(serializers.Serializer):
    fonds = serializers.SerializerMethodField()
    subfonds = serializers.SerializerMethodField()
    series = serializers.SerializerMethodField()
    container = serializers.SerializerMethodField()
    finding_aids_entities = serializers.SerializerMethodField()

    def _get_archival_unit(self, obj):
        return obj.get('archival_unit')

    def get_fonds(self, obj):
        archival_unit = self._get_archival_unit(obj)
        if archival_unit is None:
            return None
        return WorkflowArchivalUnitSerializer(archival_unit.get_fonds()).data

    def get_subfonds(self, obj):
        archival_unit = self._get_archival_unit(obj)
        if archival_unit is None:
            return None

        subfonds = archival_unit.get_subfonds()
        if subfonds is None:
            return None

        return WorkflowArchivalUnitSerializer(subfonds).data

    def get_series(self, obj):
        archival_unit = self._get_archival_unit(obj)
        if archival_unit is None:
            return None
        return WorkflowArchivalUnitSerializer(archival_unit).data

    def get_container(self, obj):
        container = obj.get('container')
        if container is None:
            return None
        return WorkflowContainerSerializer(container).data

    def get_finding_aids_entities(self, obj):
        finding_aids_entity = obj.get('finding_aids_entity')
        container = obj.get('container')

        if finding_aids_entity is not None:
            entities = [finding_aids_entity]
        elif container is not None:
            entities = FindingAidsEntity.objects.filter(
                container=container
            ).order_by('folder_no', 'sequence_no', 'id')
        else:
            entities = FindingAidsEntity.objects.none()

        return WorkflowFindingAidsEntitySerializer(entities, many=True).data
