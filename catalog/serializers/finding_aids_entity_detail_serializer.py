"""
Serializers for detailed Finding Aids Entity catalog views.

This module defines a comprehensive, read-only serialization layer
used by the public catalog to display full descriptive metadata
for archival folders and items.

The serializers here:
    - normalize deeply relational archival data
    - resolve authority-controlled entities (persons, places, subjects, etc.)
    - compute derived display fields (citation, digital identifiers, access copies)
    - are optimized for read-only catalog presentation
"""

from rest_framework import serializers

from archival_unit.models import ArchivalUnit
from authority.serializers import PersonSerializer, CorporationSerializer, CountrySerializer, PlaceSerializer, \
    LanguageSerializer, GenreSerializer, SubjectSerializer
from container.models import Container
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity, FindingAidsEntityAlternativeTitle, FindingAidsEntityDate, \
    FindingAidsEntityCreator, FindingAidsEntityPlaceOfCreation, FindingAidsEntitySubject, \
    FindingAidsEntityAssociatedPerson, FindingAidsEntityAssociatedCorporation, FindingAidsEntityAssociatedPlace, \
    FindingAidsEntityLanguage, FindingAidsEntityExtent


class ArchivalUnitSerializer(serializers.ModelSerializer):
    """
    Lightweight representation of an archival unit linked to a finding aid.

    Includes catalog-level identifiers and normalized title fields
    for display and navigation.
    """

    catalog_id = serializers.SlugRelatedField(slug_field='catalog_id', source='isad', read_only=True)

    class Meta:
        model = ArchivalUnit
        fields = ['id', 'catalog_id', 'reference_code', 'title', 'title_original', 'title_full']


class ContainerSerializer(serializers.ModelSerializer):
    """
    Serializer for physical or logical containers holding finding aids entities.

    Used to expose container identifiers, carrier type,
    and digital availability status.
    """

    carrier_type = serializers.SlugRelatedField(slug_field='type', read_only=True)

    class Meta:
        model = Container
        fields = ['id', 'container_no', 'barcode', 'digital_version_exists', 'carrier_type']


class AlternativeTitleSerializer(serializers.ModelSerializer):
    """
    Represents alternative or supplied titles for a finding aids entity.
    """

    class Meta:
        model = FindingAidsEntityAlternativeTitle
        fields = ['alternative_title', 'title_given']


class DateSerializer(serializers.ModelSerializer):
    """
    Serializer for normalized date ranges associated with a finding aids entity.
    """

    date_type = serializers.SlugRelatedField(slug_field='type', read_only=True)

    class Meta:
        model = FindingAidsEntityDate
        fields = ['date_from', 'date_to', 'date_type']


class CreatorSerializer(serializers.ModelSerializer):
    """
    Serializer for creators or collectors associated with a finding aids entity.

    Converts internal role codes into human-readable values.
    """

    role = serializers.SerializerMethodField()

    def get_role(self, obj):
        """
        Maps internal creator role codes to display labels.
        """
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
    """
    Serializer for persons associated with a finding aids entity
    in a non-primary (contextual) role.
    """

    associated_person = PersonSerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedPerson
        fields = ['associated_person', 'role']


class AssociatedCorporationSerializer(serializers.ModelSerializer):
    """
    Serializer for corporations associated with a finding aids entity
    in a non-primary (contextual) role.
    """

    associated_corporation = CorporationSerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        fields = ['associated_corporation', 'role']


class AssociatedCountrySerializer(serializers.ModelSerializer):
    """
    Serializer for countries associated with a finding aids entity
    in a non-primary (contextual) role.
    """
    associated_country = CountrySerializer(read_only=True)
    role = serializers.SlugRelatedField(slug_field='role', read_only=True)

    class Meta:
        model = FindingAidsEntityAssociatedCorporation
        fields = ['associated_country', 'role']


class AssociatedPlaceSerializer(serializers.ModelSerializer):
    """
    Serializer for places associated with a finding aids entity
    in a non-primary (contextual) role.
    """
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


class DigitalVersionSerializer(serializers.ModelSerializer):
    """
    Serializer for digital versions.

    Excludes internal identifiers and exposes only
    catalog-relevant metadata.
    """
    class Meta:
        model = DigitalVersion
        exclude = ['id',]


class FindingAidsEntityDetailSerializer(serializers.ModelSerializer):
    """
    Full-detail serializer for a Finding Aids Entity.

    This serializer provides the canonical public representation
    of archival folders and items in the institutional catalog.

    Responsibilities:
        - aggregate descriptive metadata
        - resolve authority-controlled relations
        - compute catalog-specific display fields
        - expose digital access information
        - generate human-readable citations

    This serializer is read-only and intended exclusively
    for public catalog consumption.
    """
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
    digital_version_online = serializers.SerializerMethodField()
    access_copies = serializers.SerializerMethodField()

    def get_description_level(self, obj):
        """
        Returns a human-readable description level label.

        Maps internal codes:
            L1 → Level 1
            L2 → Level 2
        """
        dl = {'L1': 'Level 1', 'L2': 'Level 2'}
        return dl[obj.description_level]

    def get_level(self, obj):
        """
        Returns a human-readable level label.

        Maps internal codes:
            F → Folder
            I → Item
        """
        fl = {'F': 'Folder', 'I': 'Item'}
        return fl[obj.level]

    def get_digital_version_identifier(self, obj):
        """
        Computes a stable identifier used for digital object references.

        Resolution order:
            1. Folder-level digital version identifier
            2. Container barcode (if available)
            3. Container label
            4. Generated container reference code

        This identifier is used for:
            - IIIF manifests
            - download references
            - viewer integration
        """
        archival_unit_ref_code = obj.archival_unit.reference_code.replace(" ", "_")

        # Folder level indicator
        if obj.digital_version_exists:
            return "%s-%04d-%03d" % (archival_unit_ref_code, obj.container.container_no, obj.folder_no)

        # Container level indicator
        if obj.container.digital_version_exists:
            if obj.container.barcode:
                return obj.container.barcode
            else:
                if obj.container.container_label:
                    return obj.container.container_label
                else:
                    return "%s-%04d" % (archival_unit_ref_code, obj.container.container_no)

    def get_citation(self, obj):
        """
        Constructs a human-readable archival citation string.

        The citation includes:
            - title (quoted or bracketed as appropriate)
            - date or date range
            - archival reference code
            - series / subfonds / fonds hierarchy
            - institutional attribution

        The resulting string is suitable for
        scholarly and catalog citation use.
        """
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

    def get_digital_version_online(self, obj):
        """
        Indicates whether at least one digital version
        of the entity is available online.
        """
        return obj.digital_versions.filter(available_online=True).count() > 0

    def get_access_copies(self, obj):
        """
        Returns serialized access-level digital copies.

        Only digital versions marked as access-level ('A')
        are included in the response.
        """
        digital_versions = obj.digital_versions.filter(level='A')
        serializer = DigitalVersionSerializer(instance=digital_versions, many=True)
        return serializer.data

    class Meta:
        model = FindingAidsEntity
        fields = '__all__'
