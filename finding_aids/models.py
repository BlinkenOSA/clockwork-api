import datetime
import uuid as uuid

from django.utils import timezone

from django.db import models
from django_date_extensions.fields import ApproximateDateField
from hashids import Hashids
from model_clone import CloneMixin

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class FindingAidsEntity(CloneMixin, DetectProtectedMixin, models.Model):
    """
    Core model representing a finding aids entity.

    A finding aids entity's description level can be either:
        - Level 1 (L1). The record can either represent a Folder or an Item record, but it is joined to
          (and sequentialy created directly under) the container record.
        - Level 2 (L2). The record can only represent an Item record. This selection allows you to define, under which
          folder is the item record can be found.

    A finding aids entity describes either:
        - a folder-level unit, or
        - an item-level unit

    within an archival container. The model supports rich descriptive
    metadata, controlled vocabularies, publication workflow, cloning,
    and digital version tracking.
    """

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, db_index=True)
    archival_unit = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.PROTECT, db_index=True)
    container = models.ForeignKey('container.Container', blank=True, null=True, on_delete=models.PROTECT, db_index=True)
    original_locale = models.ForeignKey('controlled_list.Locale', blank=True, null=True, on_delete=models.PROTECT)
    legacy_id = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    archival_reference_code = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    old_id = models.CharField(max_length=12, blank=True, null=True)
    catalog_id = models.CharField(max_length=12, blank=True, null=True, db_index=True)

    DESCRIPTION_LEVEL = [('L1', 'Level 1'), ('L2', 'Level 2')]
    description_level = models.CharField(max_length=2, choices=DESCRIPTION_LEVEL, default='L1')

    FINDING_AIDS_LEVEL = [('F', 'Folder'), ('I', 'Item')]
    level = models.CharField(max_length=1, choices=FINDING_AIDS_LEVEL, default='F')

    # Template fields
    is_template = models.BooleanField(default=False, db_index=True)
    template_name = models.CharField(max_length=100, blank=True, null=True)

    # Required fields
    folder_no = models.IntegerField(default=0)
    sequence_no = models.IntegerField(default=0, blank=True, null=True)

    title = models.CharField(max_length=300)
    title_given = models.BooleanField(default=False)
    title_original = models.CharField(max_length=300, blank=True, null=True)

    date_from = ApproximateDateField(blank=True)
    date_to = ApproximateDateField(blank=True, null=True)
    date_ca_span = models.IntegerField(blank=True, default=0)

    contents_summary = models.TextField(blank=True, null=True)
    contents_summary_original = models.TextField(blank=True, null=True)

    # Optional fields
    administrative_history = models.TextField(blank=True, null=True)
    administrative_history_original = models.TextField(blank=True, null=True)

    primary_type = models.ForeignKey('controlled_list.PrimaryType', default=1, on_delete=models.PROTECT, db_index=True)
    genre = models.ManyToManyField('authority.Genre', blank=True)

    # Associated Fields
    spatial_coverage_country = models.ManyToManyField('authority.Country', blank=True,
                                                      related_name='spatial_coverage_countries')
    spatial_coverage_place = models.ManyToManyField('authority.Place', blank=True,
                                                    related_name='spatial_coverage_places')

    # Subject Fields
    subject_person = models.ManyToManyField('authority.Person', blank=True, related_name='subject_poeple')
    subject_corporation = models.ManyToManyField('authority.Corporation', blank=True,
                                                 related_name='subject_corporations')
    subject_heading = models.ManyToManyField('authority.Subject', blank=True)
    subject_keyword = models.ManyToManyField('controlled_list.Keyword', blank=True)

    # Extra metadata fields
    language_statement = models.TextField(blank=True, null=True)
    language_statement_original = models.TextField(blank=True, null=True)

    physical_description = models.TextField(blank=True, null=True)
    physical_description_original = models.TextField(blank=True, null=True)

    physical_condition = models.CharField(max_length=300, blank=True, null=True)

    time_start = models.DurationField(blank=True, null=True)
    time_end = models.DurationField(blank=True, null=True)
    duration = models.DurationField(blank=True, null=True)

    dimensions = models.TextField(max_length=200, blank=True, null=True)

    # Notes
    note = models.TextField(blank=True, null=True)
    note_original = models.TextField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)

    # Published
    published = models.BooleanField(default=False)

    # Digital Version
    digital_version_exists = models.BooleanField(default=False, db_index=True)
    digital_version_creation_date = models.DateField(blank=True, null=True)
    digital_version_technical_metadata = models.TextField(blank=True, null=True)
    digital_version_research_cloud = models.BooleanField(default=False, db_index=True)
    digital_version_research_cloud_path = models.TextField(blank=True, null=True)
    digital_version_online = models.BooleanField(default=False, db_index=True)

    # Access Rights
    access_rights = models.ForeignKey('controlled_list.AccessRight', on_delete=models.PROTECT,
                                      blank=True, null=True, default=1)
    access_rights_restriction_date = models.DateField(blank=True, null=True)
    access_rights_restriction_explanation = models.TextField(blank=True, null=True)

    confidential_display_text = models.CharField(max_length=300, blank=True, null=True)
    confidential = models.BooleanField(default=False)

    user_published = models.CharField(max_length=100, blank=True)
    date_published = models.DateTimeField(blank=True, null=True, db_index=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True, db_index=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, db_index=True)

    # Clone fields
    _clone_excluded_fields = ['id', 'uuid', 'legacy_id', 'archival_reference_code', 'old_id', 'catalog_id', 'published']
    _clone_linked_m2m_fields = ['genre', 'spatial_coverage_country', 'spatial_coverage_place',
                                'subject_person', 'subject_corporation', 'subject_keyword']
    _clone_m2o_or_o2m_fields = [
        'findingaidsentityalternativetitle_set',
        'findingaidsentitydate_set',
        'findingaidsentitycreator_set',
        'findingaidsentityidentifier_set',
        'findingaidsentityplaceofcreation_set',
        'findingaidsentitysubject_set',
        'findingaidsentityassociatedperson_set',
        'findingaidsentityassociatedcorporation_set',
        'findingaidsentityassociatedcountry_set',
        'findingaidsentityassociatedplace_set',
        'findingaidsentityextent_set',
        'findingaidsentitylanguage_set'
    ]

    class Meta:
        db_table = 'finding_aids_entities'

    @property
    def available_online(self):
        """
        Returns True if any related digital version is available online.
        """
        return self.digital_versions.filter(available_online=True).count() > 0

    @property
    def restricted(self):
        """
        Returns True if access rights are marked as restricted.
        """
        return self.access_rights.statement == 'Restricted'

    def publish(self, user):
        """
        Publishes the finding aids entity.
        """
        self.published = True
        self.user_published = user.username
        self.date_published = timezone.now()
        self.save()

    def unpublish(self):
        """
        Unpublishes the finding aids entity.
        """
        self.published = False
        self.user_published = ""
        self.date_published = None
        self.save()

    def set_confidential(self):
        """
        Marks the entity as confidential.
        """
        self.confidential = True
        self.save()

    def set_non_confidential(self):
        """
        Removes confidential status.
        """
        self.confidential = False
        self.save()

    def set_reference_code(self):
        """
        Computes the archival reference code.

        Resolution depends on:
            - template status
            - description level (L1 / L2)
            - container, folder, and sequence numbers
        """
        if self.is_template:
            self.archival_reference_code = "%s-TEMPLATE" % self.archival_unit.reference_code
        else:
            if self.description_level == 'L1':
                self.archival_reference_code = "%s:%s/%s" % (self.container.archival_unit.reference_code,
                                                             self.container.container_no,
                                                             self.folder_no)
            else:
                self.archival_reference_code = "%s:%s/%s-%s" % (self.container.archival_unit.reference_code,
                                                                self.container.container_no,
                                                                self.folder_no,
                                                                self.sequence_no)

    def set_catalog_id(self):
        """
        Generates a stable, public-facing catalog identifier using Hashids.
        """
        if not self.is_template:
            super(FindingAidsEntity, self).save()
            # Add hashids
            hashids = Hashids(salt="blinkenosa", min_length=10)
            self.catalog_id = hashids.encode(self.id)

    def set_duration(self):
        """
        Computes duration from start and end time fields when available.
        """
        if getattr(self, 'time_end'):
            if getattr(self, 'time_start'):
                self.duration = self.time_end - self.time_start
            else:
                self.time_start = datetime.timedelta(0)
                self.duration = self.time_end

    def save(self, **kwargs):
        """
        Overrides save to keep derived fields consistent.

        Ensures:
            - date_created is set (legacy compatibility)
            - archival_reference_code is updated
            - digital version creation date is populated when applicable
            - duration is computed
            - catalog_id is generated for non-template entities
        """
        if not self.date_created:
            self.date_created = datetime.datetime.now()
        self.set_reference_code()
        if self.digital_version_exists and not self.digital_version_creation_date:
            self.digital_version_creation_date = timezone.now().date()
        self.set_duration()
        if not self.catalog_id:
            self.set_catalog_id()
        super(FindingAidsEntity, self).save()


class FindingAidsEntityAlternativeTitle(models.Model):
    """
    Stores an alternative title for a finding aids entity.

    Alternative titles support variant naming, translations, or
    cataloger-supplied titles distinct from the primary title.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)

    alternative_title = models.CharField(max_length=300)
    title_given = models.BooleanField(default=False)

    class Meta:
        db_table = 'finding_aids_alternative_titles'


class FindingAidsEntityDate(models.Model):
    """
    Stores a typed date range for a finding aids entity.

    Dates use ApproximateDateField to support imprecise values and are
    classified by a controlled DateType.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    date_from = ApproximateDateField()
    date_to = ApproximateDateField(blank=True, null=True)
    date_type = models.ForeignKey('controlled_list.DateType', on_delete=models.PROTECT)

    class Meta:
        db_table = 'finding_aids_dates'


class FindingAidsEntityCreator(models.Model):
    """
    Stores a creator entry for a finding aids entity.

    Creator records store a free-text creator name alongside a controlled
    role value (e.g. Creator vs Collector).
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    creator = models.CharField(max_length=300)
    CREATOR_ROLE = [('COL', 'Collector'), ('CRE', 'Creator')]
    role = models.CharField(max_length=3, choices=CREATOR_ROLE, default='CRE')

    class Meta:
        db_table = 'finding_aids_creators'


class FindingAidsEntityIdentifier(models.Model):
    """
    Stores an identifier for a finding aids entity.

    Identifiers support typed values (e.g. legacy ids, external references)
    using a controlled IdentifierType.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    identifier = models.CharField(max_length=50, blank=True, null=True)
    identifier_type = models.ForeignKey('controlled_list.IdentifierType', on_delete=models.PROTECT)

    class Meta:
        db_table = 'finding_aids_identifiers'


class FindingAidsEntityPlaceOfCreation(models.Model):
    """
    Stores a free-text place of creation for a finding aids entity.

    This model captures a literal place string when a controlled place
    authority record is not used or not available.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    place = models.CharField(max_length=200)

    class Meta:
        db_table = 'finding_aids_places_of_creation'


class FindingAidsEntitySubject(models.Model):
    """
    Stores a free-text subject for a finding aids entity.

    This model supports literal subject terms when controlled authority
    subjects are not used or not available.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)

    class Meta:
        db_table = 'finding_aids_subjects'


class FindingAidsEntityAssociatedPerson(models.Model):
    """
    Links a finding aids entity to an associated person authority record.

    The association may include a controlled PersonRole describing how the
    person relates to the described materials.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_person = models.ForeignKey('authority.Person', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.PersonRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_people'


class FindingAidsEntityAssociatedCorporation(models.Model):
    """
    Links a finding aids entity to an associated corporation authority record.

    The association may include a controlled CorporationRole describing how
    the corporation relates to the described materials.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_corporation = models.ForeignKey('authority.Corporation', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.CorporationRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_corporations'


class FindingAidsEntityAssociatedCountry(models.Model):
    """
    Links a finding aids entity to an associated country authority record.

    The association may include a controlled GeoRole describing how the
    location relates to the described materials.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_country = models.ForeignKey('authority.Country', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.GeoRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_countries'


class FindingAidsEntityAssociatedPlace(models.Model):
    """
    Links a finding aids entity to an associated place authority record.

    The association may include a controlled GeoRole describing how the
    place relates to the described materials.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_place = models.ForeignKey('authority.Place', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.GeoRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_places'


class FindingAidsEntityLanguage(CloneMixin, models.Model):
    """
    Links a finding aids entity to a language authority record.

    The link may include a controlled LanguageUsage describing the role of
    the language (e.g. spoken, written).
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', on_delete=models.PROTECT)
    language_usage = models.ForeignKey('controlled_list.LanguageUsage', on_delete=models.SET_NULL,
                                       blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_languages'


class FindingAidsEntityExtent(models.Model):
    """
    Stores a typed extent value for a finding aids entity.

    Extent values combine a numeric amount with a controlled ExtentUnit.
    """

    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    extent_number = models.IntegerField(blank=True, null=True)
    extent_unit = models.ForeignKey('controlled_list.ExtentUnit', on_delete=models.CASCADE)

    class Meta:
        db_table = 'finding_aids_extents'


class FindingAidsEntityRelatedMaterial(models.Model):
    """
    Represents a bidirectional "related material" relationship between entities.

    Each relationship is stored in two directions:
        - source -> destination
        - destination -> source

    The save and delete methods enforce this symmetry automatically.
    """

    id = models.AutoField(primary_key=True)
    source = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE, related_name='relationship_sources')
    destination = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE, related_name='relationship_destinations')
    relationship_source = models.CharField(max_length=300, blank=True, null=True)
    relationship_destination = models.CharField(max_length=300, blank=True, null=True)

    def save(self, **kwargs):
        """
        Saves the relationship and ensures the reverse relationship exists.

        The reverse record mirrors:
            - source/destination swapped
            - relationship labels swapped
        """

        super(FindingAidsEntityRelatedMaterial, self).save()
        # Save the other side of the relationship
        related_material, created = FindingAidsEntityRelatedMaterial.objects.get_or_create(
            source=self.destination,
            destination=self.source
        )
        related_material.relationship_source = self.relationship_destination
        related_material.relationship_destination = self.relationship_source
        related_material.save()

    def delete(self, using=None, keep_parents=False):
        """
        Deletes the relationship and removes the reverse relationship record.
        """

        # Delete the other side of the relationship
        FindingAidsEntityRelatedMaterial.objects.filter(
            source=self.destination,
            destination=self.source
        ).delete()
        super(FindingAidsEntityRelatedMaterial, self).delete()

    class Meta:
        db_table = 'finding_aids_related_materials'
        unique_together = ('id', 'source', 'destination')
