from django.db import models

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class AccessRight(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for access rights statements.

    Used to standardize access right text across records and prevent
    inconsistent free-text values.
    """

    id = models.AutoField(primary_key=True)
    statement = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.statement

    class Meta:
        db_table = 'controlled_rights_access'
        ordering = ['statement']


class ArchivalUnitTheme(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for archival unit themes.

    Themes provide a standardized way to categorize archival units for
    browsing, filtering, and discovery.
    """

    id = models.AutoField(primary_key=True)
    theme = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.theme

    class Meta:
        db_table = 'controlled_archival_unit_themes'
        ordering = ['theme']


class Building(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for building locations.

    Represents a building identifier or name used for location-based
    metadata (locations of accessioned materials and processed physical ones) and filtering.
    """

    id = models.AutoField(primary_key=True)
    building = models.CharField(max_length=50)

    def __str__(self):
        return self.building

    class Meta:
        db_table = 'controlled_building'
        ordering = ['building']


class CarrierType(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry describing a carrier type.

    Carrier types represent the physical or technical format of a container
    (e.g., Archival Box, VHS Tape, Digital Container) and may include dimensional metadata used for
    storage management and labeling.
    """

    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=100)
    type_original_language = models.CharField(max_length=100, blank=True, null=True)
    width = models.IntegerField()
    height = models.IntegerField(blank=True, null=True)
    depth = models.IntegerField(blank=True, null=True)
    old_id = models.IntegerField(blank=True, null=True)
    jasper_file = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.type

    class Meta:
        db_table = 'controlled_carrier_types'
        ordering = ['type']


class CorporationRole(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for corporate entity roles.

    Roles describe how a corporation is related to a finding aids Record (e.g., creator,
    producer, copyright holder, etc.), enabling consistent indexing and display.
    """
    id = models.AutoField(primary_key=True)
    role = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.role

    class Meta:
        db_table = 'controlled_corporation_roles'
        ordering = ['role']


class DateType(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for date types.

    Date types standardize how dates are interpreted (e.g., creation date,
    broadcast date, publication date) in descriptive metadata.
    """

    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.type

    class Meta:
        db_table = 'controlled_date_types'
        ordering = ['type']


class ExtentUnit(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for extent units.

    Extent units standardize how physical or digital extent is expressed
    (e.g., pages, reels, items, GB).
    """

    id = models.AutoField(primary_key=True)
    unit = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.unit

    class Meta:
        db_table = 'controlled_extent_units'
        ordering = ['unit']


class GeoRole(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for geographic roles.

    Roles describe how a geographic entity is related to a record
    (e.g., place of creation, place of publication), enabling consistent indexing.
    """

    id = models.AutoField(primary_key=True)
    role = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.role

    class Meta:
        db_table = 'controlled_geo_roles'
        ordering = ['role']


class IdentifierType(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for identifier types.

    Identifier types specify the meaning or scheme of an identifier
    (e.g., ISBN, ISSN), supporting validation and consistent display.
    """

    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.type.strip()

    class Meta:
        db_table = 'controlled_identifier_types'
        ordering = ['type']


class Keyword(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for descriptive keywords.

    Keywords provide standardized terms for tagging and discovery while
    preventing duplicate or near-duplicate free-text values.
    """

    id = models.AutoField(primary_key=True)
    keyword = models.CharField(unique=True, max_length=250)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.keyword.strip()

    class Meta:
        db_table = 'controlled_keywords'
        ordering = ['keyword']


class LanguageUsage(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for language usage.

    Language usage values describe how a language is used in a finding aids record (mostly audio-visual)
    (e.g., original, subtitle, dubbing), supporting consistent filtering.
    """

    id = models.AutoField(primary_key=True)
    usage = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.usage

    class Meta:
        db_table = 'controlled_language_usages'
        ordering = ['usage']


class Locale(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for locales.

    Locales use a short string primary key (locale code)
    and a unique display name for UI presentation. They determine the original
    language of cataloging.
    """

    id = models.CharField(primary_key=True, max_length=2)
    locale_name = models.CharField(unique=True, max_length=50)

    class Meta:
        db_table = 'controlled_locales'
        ordering = ['locale_name']


class Nationality(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for nationalities.

    Nationality values standardize how nationality is recorded for researchers.
    """

    id = models.AutoField(primary_key=True)
    nationality = models.CharField(unique=True, max_length=150)

    def __str__(self):
        return self.nationality

    class Meta:
        db_table = 'controlled_nationalities'
        ordering = ['nationality']


class PersonRole(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for person roles.

    Roles describe how a person is related to a finding aids record (e.g., director,
    interviewer, producer), enabling consistent indexing and display.
    """

    id = models.AutoField(primary_key=True)
    role = models.CharField(unique=True, max_length=100)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def __str__(self):
        return self.role

    class Meta:
        db_table = 'controlled_person_roles'
        ordering = ['role']


class PrimaryType(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for primary record types.

    Primary types represent a short, standardized classification used for
    grouping and filtering finding aids records at a high level. They can be
    textual, audio, moving image or still image.
    """

    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=20)

    def __str__(self):
        return self.type

    class Meta:
        db_table = 'controlled_primary_types'
        ordering = ['type']


class ReproductionRight(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for reproduction rights statements.

    Used to standardize reproduction rights text across records and prevent
    inconsistent free-text values.
    """

    id = models.AutoField(primary_key=True)
    statement = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.statement

    class Meta:
        db_table = 'controlled_rights_reproduction'
        ordering = ['statement']


class RightsRestrictionReason(models.Model, DetectProtectedMixin):
    """
    Controlled vocabulary entry for rights restriction reasons.

    Reasons describe why access or use is restricted (e.g., ethical,
    donor agreement) using standardized terms for reporting and filtering.
    """

    id = models.AutoField(primary_key=True)
    reason = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.reason

    class Meta:
        db_table = 'controlled_rights_restriction_reason'
        ordering = ['reason']
