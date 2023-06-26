from django.db import models

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class AccessRight(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    statement = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.statement

    class Meta:
        db_table = 'controlled_rights_access'
        ordering = ['statement']


class ArchivalUnitTheme(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    theme = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.theme

    class Meta:
        db_table = 'controlled_archival_unit_themes'
        ordering = ['theme']


class Building(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    building = models.CharField(max_length=50)

    def __str__(self):
        return self.building

    class Meta:
        db_table = 'controlled_building'
        ordering = ['building']


class CarrierType(models.Model, DetectProtectedMixin):
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
    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.type

    class Meta:
        db_table = 'controlled_date_types'
        ordering = ['type']


class ExtentUnit(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    unit = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.unit

    class Meta:
        db_table = 'controlled_extent_units'
        ordering = ['unit']


class GeoRole(models.Model, DetectProtectedMixin):
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
    id = models.AutoField(primary_key=True)
    usage = models.CharField(unique=True, max_length=100)

    def __str__(self):
        return self.usage

    class Meta:
        db_table = 'controlled_language_usages'
        ordering = ['usage']


class Locale(models.Model, DetectProtectedMixin):
    id = models.CharField(primary_key=True, max_length=2)
    locale_name = models.CharField(unique=True, max_length=50)

    class Meta:
        db_table = 'controlled_locales'
        ordering = ['locale_name']


class Nationality(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    nationality = models.CharField(unique=True, max_length=150)

    def __str__(self):
        return self.nationality

    class Meta:
        db_table = 'controlled_nationalities'
        ordering = ['nationality']


class PersonRole(models.Model, DetectProtectedMixin):
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
    id = models.AutoField(primary_key=True)
    type = models.CharField(unique=True, max_length=20)

    def __str__(self):
        return self.type

    class Meta:
        db_table = 'controlled_primary_types'
        ordering = ['type']


class ReproductionRight(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    statement = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.statement

    class Meta:
        db_table = 'controlled_rights_reproduction'
        ordering = ['statement']


class RightsRestrictionReason(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)
    reason = models.CharField(unique=True, max_length=200)

    def __str__(self):
        return self.reason

    class Meta:
        db_table = 'controlled_rights_restriction_reason'
        ordering = ['reason']
