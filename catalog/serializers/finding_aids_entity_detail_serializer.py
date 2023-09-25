from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from authority.serializers import PersonSerializer, CorporationSerializer, CountrySerializer, PlaceSerializer, \
    LanguageSerializer, GenreSerializer, SubjectSerializer
from container.models import Container
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAlternativeTitle, FindingAidsEntityDate, \
    FindingAidsEntityCreator, FindingAidsEntityPlaceOfCreation, FindingAidsEntitySubject, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, FindingAidsEntityAssociatedPlace, \
    FindingAidsEntityLanguage, FindingAidsEntityExtent


class ArchivalUnitSerializer(serializers.ModelSerializer):
    catalog_id = serializers.SlugRelatedField(slug_field='catalog_id', source='isad', read_only=True)

    class Meta:
        model = ArchivalUnit
        fields = ['id', 'catalog_id', 'reference_code', 'title', 'title_original', 'title_full']


class ContainerSerializer(serializers.ModelSerializer):
    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True)

    class Meta:
        model = Container
        fields = ['id', 'container_no', 'barcode', 'digital_version_exists', 'carrier_type']


class AlternativeTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityAlternativeTitle
        fields = ['alternative_title', 'title_given']


class DateSerializer(serializers.ModelSerializer):
    date_type = serializers.SlugRelatedField(slug_field='type', read_only=True)

    class Meta:
        model = FindingAidsEntityDate
        fields = ['date_from', 'date_to', 'date_type']


class CreatorSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        if obj.role == 'COL':
            return 'Collector'
        else:
            return 'Creator'

    class Meta:
        model = FindingAidsEntityCreator
        fields = ['creator', 'role']


class PlaceOfCreationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntityPlaceOfCreation
        fields = ['place']


class FASubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = FindingAidsEntitySubject
        fields = ['subject']


class AssociatedPersonSerializer(serializers.ModelSerializer):
    associated_person = PersonSerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedPerson
        fields = ['associated_person', 'role']


class AssociatedCorporationSerializer(serializers.ModelSerializer):
    associated_corporation = CorporationSerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        fields = ['associated_corporation', 'role']


class AssociatedCountrySerializer(serializers.ModelSerializer):
    associated_country = CountrySerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        fields = ['associated_country', 'role']


class AssociatedPlaceSerializer(serializers.ModelSerializer):
    associated_place = PlaceSerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedPlace
        fields = ['associated_place', 'role']


class FALanguageSerializer(serializers.ModelSerializer):
    language = LanguageSerializer(read_only=True)
    language_usage = serializers.SlugRelatedField(slug_field='usage', read_only=True)

    class Meta:
        model = FindingAidsEntityLanguage
        fields = ['language', 'language_usage']


class FAExtentSerializer(serializers.ModelSerializer):
    extent_unit = serializers.SlugRelatedField(slug_field='unit', read_only=True)

    class Meta:
        model = FindingAidsEntityExtent
        fields = ['extent_number', 'extent_unit']


class FindingAidsEntityDetailSerializer(serializers.ModelSerializer):
    archival_unit = ArchivalUnitSerializer()
    container = ContainerSerializer()
    primary_type = serializers.SlugRelatedField(slug_field='type', read_only=True)
    genre = GenreSerializer(many=True)
    level = serializers.SerializerMethodField()
    description_level = serializers.SerializerMethodField()
    access_rights = serializers.SlugRelatedField(slug_field='statement', read_only=True)
    spatial_coverage_country = CountrySerializer(many=True)
    spatial_coverage_place = PlaceSerializer(many=True)
    subject_person = PersonSerializer(many=True)
    subject_corporation = CorporationSerializer(many=True)
    subject_heading = SubjectSerializer(many=True)
    subject_keyword = serializers.SlugRelatedField(many=True, slug_field='keyword', read_only=True)
    title_alternative = AlternativeTitleSerializer(many=True, source='findingaidsentityalternativetitle_set')
    dates = DateSerializer(many=True, source='findingaidsentitydate_set')
    creator = CreatorSerializer(many=True, source='findingaidsentitycreator_set')
    place_of_creation = PlaceOfCreationSerializer(many=True, source='findingaidsentityplaceofcreation_set')
    subject_free_text = FASubjectSerializer(many=True, source='findingaidsentitysubject_set')
    added_person = AssociatedPersonSerializer(many=True, source='findingaidsentityassociatedperson_set')
    added_corporation = AssociatedCorporationSerializer(many=True, source='findingaidsentityassociatedcorporation_set')
    added_country = AssociatedCountrySerializer(many=True, source='findingaidsentityassociatedcountry_set')
    added_place = AssociatedPlaceSerializer(many=True, source='findingaidsentityassociatedplace_set')
    digital_version_identifier = serializers.SerializerMethodField()
    languages = FALanguageSerializer(many=True, source='findingaidsentitylanguage_set')
    citation = serializers.SerializerMethodField()

    def get_description_level(self, obj):
        dl = {'L1': 'Level 1', 'L2': 'Level 2'}
        return dl[obj.description_level]

    def get_level(self, obj):
        fl = {'F': 'Folder', 'I': 'Item'}
        return fl[obj.level]

    def get_digital_version_identifier(self, obj):
        archival_unit_ref_code = obj.archival_unit.reference_code.replace(" ", "_")

        # Folder level indicator
        if obj.digital_version_exists:
            return "%s-%03d-%03d" % (archival_unit_ref_code, obj.container.container_no, obj.folder_no)

        # Container level indicator
        if obj.container.digital_version_exists:
            if obj.container.barcode:
                return obj.container.barcode
            else:
                if obj.container.container_label:
                    return obj.container.container_label
                else:
                    return "%s-%03d" % (archival_unit_ref_code, obj.container.container_no)

    def get_citation(self, obj):
        citation = []

        # Title
        if obj.title_given:
            citation.append("[%s]" % obj.title)
        else:
            if obj.primary_type.type == 'Still Image':
                citation.append('"%s"' % obj.title)
            else:
                citation.append(obj.title)
        citation.append(', ')

        # Date
        if obj.date_to:
            citation.append("%s - %s" % (str(obj.date_from), str(obj.date_to)))
        else:
            citation.append(str(obj.date_from))
        citation.append('; ')

        # Ref. code
        citation.append(obj.archival_reference_code)
        citation.append('; ')

        # Series
        citation.append(obj.archival_unit.title)
        citation.append('; ')

        # Subfonds
        if obj.archival_unit.subfonds != 0:
            citation.append(obj.archival_unit.parent.title)
            citation.append('; ')

        # Fonds
        citation.append(obj.archival_unit.parent.parent.title)
        citation.append('; ')

        # OSA
        citation.append("Vera and Donald Blinken Open Society Archives at Central European University, Budapest")

        return "".join(citation)

    class Meta:
        model = FindingAidsEntity
        fields = '__all__'
