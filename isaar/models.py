from __future__ import unicode_literals

import uuid as uuid
from django.db import models
from django_date_extensions.fields import ApproximateDateField


class Isaar(models.Model):
    """
    Core model representing an ISAAR (CPF) authority record.

    An ISAAR record describes an authority entity (e.g., corporate body, person,
    family) with required identity fields, descriptive notes, and control
    metadata used for workflow and provenance.

    Related models store repeatable structures such as parallel/other/
    standardized names, identifiers, and places.
    """

    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    old_id = models.CharField(max_length=20, blank=True, null=True)
    legacy_id = models.CharField(max_length=20, blank=True, null=True)

    # Required Values
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=1)
    date_existence_from = ApproximateDateField()
    date_existence_to = ApproximateDateField(blank=True)

    # Description
    function = models.TextField(blank=True, null=True)
    general_context = models.TextField(blank=True, null=True)
    legal_status = models.CharField(max_length=200, blank=True, null=True)
    history = models.TextField(blank=True, null=True)
    mandate = models.TextField(blank=True, null=True)
    internal_structure = models.TextField(blank=True, null=True)

    # Control
    language = models.ManyToManyField('authority.Language', blank=True)
    level_of_detail = models.CharField(max_length=10, default='Minimal')
    status = models.CharField(max_length=10, default='Draft')
    institution_identifier = models.CharField(max_length=10, default='HU OSA')
    source = models.TextField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    convention = models.TextField(blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    user_approved = models.CharField(max_length=100, blank=True)
    date_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'isaar_records'
        ordering = ['name']


class IsaarRelationship(models.Model):
    """
    Controlled vocabulary for relationships between name forms.

    Relationship terms qualify :class:`IsaarOtherName` entries (e.g., earlier
    name, later name, acronym). The allowed values are defined by the data in
    this table.
    """

    id = models.AutoField(primary_key=True)
    relationship = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'isaar_relationships'


class IsaarParallelName(models.Model):
    """
    Stores a parallel (equivalent) name for an ISAAR record.

    Parallel names typically represent alternative authorized forms in other
    languages/scripts that are considered equivalent to the main ISAAR name.
    """

    id = models.AutoField(primary_key=True)
    isaar = models.ForeignKey('Isaar', on_delete=models.CASCADE)
    name = models.CharField(max_length=250)

    class Meta:
        db_table = 'isaar_parallel_names'
        unique_together = ('isaar', 'name')


class IsaarOtherName(models.Model):
    """
    Stores an "other" (variant) name for an ISAAR record.

    Other names capture variants such as former/later names, abbreviations, or
    informal forms. Optionally, a relationship term and year range can be used
    to contextualize the variant.
    """

    id = models.AutoField(primary_key=True)
    isaar = models.ForeignKey('Isaar', on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    relationship = models.ForeignKey('IsaarRelationship', blank=True, null=True, on_delete=models.SET_NULL)
    year_from = models.IntegerField(blank=True, null=True)
    year_to = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'isaar_other_names'
        unique_together = ('isaar', 'name')


class IsaarStandardizedName(models.Model):
    """
    Stores a standardized name form for an ISAAR record.

    Standardized names store normalized variants produced according to a
    particular standard or rule set (recorded in the optional `standard` field).
    """

    id = models.AutoField(primary_key=True)
    isaar = models.ForeignKey('Isaar', on_delete=models.CASCADE)
    name = models.CharField(max_length=250)
    standard = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'isaar_standardized_names'
        unique_together = ('isaar', 'name')


class IsaarCorporateBodyIdentifier(models.Model):
    """
    Stores an identifier for an ISAAR record.

    Identifiers may be internal or external (e.g., registry identifiers) and can
    optionally record the rule/standard used to assign or format the value.
    """

    id = models.AutoField(primary_key=True)
    isaar = models.ForeignKey('Isaar', on_delete=models.CASCADE)
    identifier = models.CharField(max_length=200)
    rule = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'isaar_corporate_body_identifiers'


class IsaarPlaceQualifier(models.Model):
    """
    Controlled vocabulary for qualifying place associations.

    Place qualifiers refine the meaning of a place association (e.g.,
    headquarters, seat, place of activity). The allowed values are defined by
    the data in this table.
    """

    id = models.BigIntegerField(primary_key=True)
    qualifier = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'isaar_place_qualifiers'


class IsaarPlace(models.Model):
    """
    Stores a place association for an ISAAR record.

    Place associations link an ISAAR entity to a place string, optionally
    qualified (via :class:`IsaarPlaceQualifier`) and bounded by a year range.
    """

    id = models.AutoField(primary_key=True)
    isaar = models.ForeignKey('Isaar', on_delete=models.CASCADE)
    place = models.CharField(max_length=200)
    place_qualifier = models.ForeignKey('IsaarPlaceQualifier', blank=True, null=True, on_delete=models.SET_NULL)
    year_from = models.IntegerField(blank=True, null=True)
    year_to = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'isaar_places'
        unique_together = ('isaar', 'place')
