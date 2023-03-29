import datetime
import uuid as uuid

from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from django.db import models
from django_date_extensions.fields import ApproximateDateField
from hashids import Hashids
from model_clone import CloneMixin

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class FindingAidsEntity(CloneMixin, DetectProtectedMixin, models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4)
    archival_unit = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.PROTECT, db_index=True)
    container = models.ForeignKey('container.Container', blank=True, null=True, on_delete=models.PROTECT, db_index=True)
    original_locale = models.ForeignKey('controlled_list.Locale', blank=True, null=True, on_delete=models.PROTECT)
    legacy_id = models.CharField(max_length=200, blank=True, null=True, db_index=True)
    archival_reference_code = models.CharField(max_length=50, blank=True, null=True, db_index=True)

    old_id = models.CharField(max_length=12, blank=True, null=True)
    catalog_id = models.CharField(max_length=12, blank=True, null=True)

    DESCRIPTION_LEVEL = [('L1', 'Level 1'), ('L2', 'Level 2')]
    description_level = models.CharField(max_length=2, choices=DESCRIPTION_LEVEL, default='L1')

    FINDING_AIDS_LEVEL = [('F', 'Folder'), ('I', 'Item')]
    level = models.CharField(max_length=1, choices=FINDING_AIDS_LEVEL, default='F')

    # Template fields
    is_template = models.BooleanField(default=False)
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

    primary_type = models.ForeignKey('controlled_list.PrimaryType', default=1, on_delete=models.PROTECT)
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

    physical_condition = models.CharField(max_length=200, blank=True, null=True)

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
    digital_version_exists = models.BooleanField(default=False)
    digital_version_creation_date = models.DateField(blank=True, null=True)
    digital_version_technical_metadata = models.TextField(blank=True, null=True)
    digital_version_research_cloud = models.BooleanField(default=False)
    digital_version_research_cloud_path = models.TextField(blank=True, null=True)
    digital_version_online = models.BooleanField(default=False)

    confidential_display_text = models.CharField(max_length=300, blank=True, null=True)
    confidential = models.BooleanField(default=False)

    user_published = models.CharField(max_length=100, blank=True)
    date_published = models.DateTimeField(blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True)

    # Clone fields
    _clone_excluded_model_fields = ['id', 'uuid', 'legacy_id', 'archival_reference_code', 'old_id', 'catalog_id']
    _clone_many_to_many_fields = ['genre', 'spatial_coverage_country', 'spatial_coverage_place',
                                  'subject_person', 'subject_corporation', 'subject_keyword']
    _clone_many_to_one_or_one_to_many_fields = ['archival_unit', 'container', 'original_locale', 'primary_type']

    class Meta:
        db_table = 'finding_aids_entities'


    def publish(self, user):
        self.published = True
        self.user_published = user.username
        self.date_published = timezone.now()
        self.save()

    def unpublish(self):
        self.published = False
        self.user_published = ""
        self.date_published = None
        self.save()

    def set_confidential(self):
        self.confidential = True
        self.save()

    def set_non_confidential(self):
        self.confidential = False
        self.save()

    def set_reference_code(self):
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
        if not self.is_template:
            # Add hashids
            hashids = Hashids(salt="blinkenosa", min_length=10)
            if not self.catalog_id:
                self.catalog_id = hashids.encode(self.id)

    def save(self, **kwargs):
        if not self.date_created:
            self.date_created = datetime.datetime.now()
        self.set_reference_code()
        self.set_catalog_id()
        if self.digital_version_exists and not self.digital_version_creation_date:
            self.digital_version_creation_date = datetime.datetime.now()
        super(FindingAidsEntity, self).save()


class FindingAidsEntityAlternativeTitle(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)

    alternative_title = models.CharField(max_length=300)
    title_given = models.BooleanField(default=False)

    class Meta:
        db_table = 'finding_aids_alternative_titles'


class FindingAidsEntityDate(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    date_from = ApproximateDateField()
    date_to = ApproximateDateField(blank=True)
    date_type = models.ForeignKey('controlled_list.DateType', on_delete=models.PROTECT)

    class Meta:
        db_table = 'finding_aids_dates'


class FindingAidsEntityCreator(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    creator = models.CharField(max_length=300)
    CREATOR_ROLE = [('COL', 'Collector'), ('CRE', 'Creator')]
    role = models.CharField(max_length=3, choices=CREATOR_ROLE, default='CRE')

    class Meta:
        db_table = 'finding_aids_creators'


class FindingAidsEntityPlaceOfCreation(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    place = models.CharField(max_length=200)

    class Meta:
        db_table = 'finding_aids_places_of_creation'


class FindingAidsEntitySubject(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)

    class Meta:
        db_table = 'finding_aids_subjects'


class FindingAidsEntityAssociatedPerson(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_person = models.ForeignKey('authority.Person', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.PersonRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_people'


class FindingAidsEntityAssociatedCorporation(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_corporation = models.ForeignKey('authority.Corporation', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.CorporationRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_corporations'


class FindingAidsEntityAssociatedCountry(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_country = models.ForeignKey('authority.Country', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.GeoRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_countries'


class FindingAidsEntityAssociatedPlace(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    associated_place = models.ForeignKey('authority.Place', on_delete=models.PROTECT)
    role = models.ForeignKey('controlled_list.GeoRole', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_associated_places'


class FindingAidsEntityLanguage(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    language = models.ForeignKey('authority.Language', on_delete=models.PROTECT)
    language_usage = models.ForeignKey('controlled_list.LanguageUsage', on_delete=models.SET_NULL,
                                       blank=True, null=True)

    class Meta:
        db_table = 'finding_aids_languages'


class FindingAidsEntityExtent(models.Model):
    id = models.AutoField(primary_key=True)
    fa_entity = models.ForeignKey('FindingAidsEntity', on_delete=models.CASCADE)
    extent_number = models.IntegerField(blank=True, null=True)
    extent_unit = models.ForeignKey('controlled_list.ExtentUnit', on_delete=models.CASCADE)

    class Meta:
        db_table = 'finding_aids_extents'
