from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django_date_extensions.fields import ApproximateDateField
from hashids import Hashids


class Isad(models.Model):
    """
    Core model representing an ISAD(G) descriptive record.

    The ISAD record is bound 1:1 to an :class:`archival_unit.ArchivalUnit` and
    stores descriptive, access, rights, and publication metadata for fonds,
    subfonds, and series levels.

    Some identity fields (e.g., ``title`` and ``reference_code``) are derived
    from the linked archival unit on save. The ``catalog_id`` is a stable
    public-facing identifier computed from the archival unit hierarchy.
    """

    id = models.AutoField(primary_key=True)
    catalog_id = models.CharField(max_length=20, blank=True, null=True, db_index=True)
    archival_unit = models.OneToOneField('archival_unit.ArchivalUnit', on_delete=models.PROTECT, related_name='isad')
    original_locale = models.ForeignKey('controlled_list.Locale', blank=True, null=True, on_delete=models.PROTECT)
    legacy_id = models.IntegerField(blank=True, null=True)

    # Required fields
    title = models.CharField(max_length=255)
    reference_code = models.CharField(max_length=30, db_index=True)

    DESCRIPTION_LEVEL = [('F', 'Fonds'), ('SF', 'Subfonds'), ('S', 'Series')]
    description_level = models.CharField(max_length=10, choices=DESCRIPTION_LEVEL)
    year_from = models.IntegerField()
    year_to = models.IntegerField(blank=True, null=True)
    isaar = models.ForeignKey('isaar.Isaar', on_delete=models.PROTECT, blank=True, null=True)
    language = models.ManyToManyField('authority.Language')
    accruals = models.BooleanField(default=False)

    access_rights = models.ForeignKey('controlled_list.AccessRight', on_delete=models.PROTECT,
                                      blank=True, null=True)
    access_rights_legacy = models.TextField(blank=True, null=True)
    access_rights_legacy_original = models.TextField(blank=True, null=True)
    reproduction_rights = models.ForeignKey('controlled_list.ReproductionRight', on_delete=models.PROTECT,
                                            blank=True, null=True)
    reproduction_rights_legacy = models.TextField(blank=True, null=True)
    reproduction_rights_legacy_original = models.TextField(blank=True, null=True)
    rights_restriction_reason = models.ForeignKey('controlled_list.RightsRestrictionReason', on_delete=models.PROTECT,
                                                  blank=True, null=True)

    # Identity
    date_predominant = models.CharField(max_length=200, blank=True, null=True)

    carrier_estimated = models.TextField(blank=True, null=True)
    carrier_estimated_original = models.TextField(blank=True, null=True)

    # Context
    administrative_history = models.TextField(blank=True, null=True)
    administrative_history_original = models.TextField(blank=True, null=True)
    archival_history = models.TextField(blank=True, null=True)
    archival_history_original = models.TextField(blank=True, null=True)

    # Content
    scope_and_content_abstract = models.TextField(blank=True, null=True)
    scope_and_content_abstract_original = models.TextField(blank=True, null=True)
    scope_and_content_narrative = models.TextField(blank=True, null=True)
    scope_and_content_narrative_original = models.TextField(blank=True, null=True)
    appraisal = models.TextField(blank=True, null=True)
    appraisal_original = models.TextField(blank=True, null=True)
    system_of_arrangement_information = models.TextField(blank=True, null=True)
    system_of_arrangement_information_original = models.TextField(blank=True, null=True)

    # Access & Use
    embargo = ApproximateDateField(blank=True)
    physical_characteristics = models.TextField(blank=True, null=True)
    physical_characteristics_original = models.TextField(blank=True, null=True)

    # Allied Materials
    publication_note = models.TextField(blank=True, null=True)
    publication_note_original = models.TextField(blank=True, null=True)

    # Notes
    note = models.TextField(blank=True, null=True)
    note_original = models.TextField(blank=True, null=True)
    internal_note = models.TextField(blank=True, null=True)
    internal_note_original = models.TextField(blank=True, null=True)
    archivists_note = models.TextField(blank=True, null=True)
    archivists_note_original = models.TextField(blank=True, null=True)
    rules_conventions = models.TextField(blank=True, null=True)

    # Published
    published = models.BooleanField(default=False)
    user_published = models.CharField(max_length=100, blank=True)
    date_published = models.DateTimeField(blank=True, null=True, db_index=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True, db_index=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, db_index=True)

    class Meta:
        db_table = 'isad_recrods'
        indexes = [
            models.Index(fields=['published']),
            models.Index(fields=['archival_unit'])
        ]

    def _get_catalog_id(self):
        """
        Computes the stable catalog identifier for the linked archival unit.

        The identifier is generated via Hashids using a numeric composite derived
        from the archival unit hierarchy (fonds/subfonds/series).

        Returns
        -------
        str
            Hashids-encoded catalog identifier.
        """
        hashids = Hashids(salt="osaarchives", min_length=8)
        return hashids.encode(self.archival_unit.fonds * 1000000 +
                              self.archival_unit.subfonds * 1000 +
                              self.archival_unit.series)

    def publish(self, user):
        """
        Publishes the ISAD record.

        Parameters
        ----------
        user : django.contrib.auth.models.User
            User performing the publish action. The username is stored in
            ``user_published``.
        """
        self.published = True
        self.user_published = user.username
        self.date_published = timezone.now()
        self.save()

    def unpublish(self):
        """
        Unpublishes the ISAD record.
        """
        self.published = False
        self.user_published = ""
        self.date_published = None
        self.save()

    def save(self, **kwargs):
        """
        Overrides save to keep derived fields consistent.

        Ensures:
            - ``title`` matches the linked archival unit title
            - ``reference_code`` matches the linked archival unit reference code
            - ``catalog_id`` is generated from the archival unit hierarchy
        """
        self.title = self.archival_unit.title
        self.reference_code = self.archival_unit.reference_code
        self.catalog_id = self._get_catalog_id()
        super(Isad, self).save()


class IsadCreator(models.Model):
    """
    Stores a creator entry for an ISAD record.

    Creators are stored as free-text values associated with the parent
    :class:`Isad`.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', on_delete=models.CASCADE)
    creator = models.CharField(max_length=300)

    class Meta:
        db_table = 'isad_creators'


class IsadExtent(models.Model):
    """
    Stores a typed extent value for an ISAD record.

    Extent records combine a numeric amount with a controlled extent unit and
    may optionally mark the value as approximate.

    Notes
    -----
    Uniqueness is enforced per ISAD record and extent unit via
    ``unique_together = (('isad', 'extent_unit'),)``.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', on_delete=models.CASCADE)
    approx = models.BooleanField(default=False)  # This field type is a guess.
    extent_number = models.IntegerField()
    extent_unit = models.ForeignKey('controlled_list.ExtentUnit', on_delete=models.PROTECT)

    class Meta:
        db_table = 'isad_extents'
        unique_together = (('isad', 'extent_unit'),)


class IsadCarrier(models.Model):
    """
    Stores a carrier (physical unit) count for an ISAD record.

    Carrier records capture the number of carriers and their type using a
    controlled carrier type.

    Notes
    -----
    Uniqueness is enforced per ISAD record and carrier type via
    ``unique_together = (('isad', 'carrier_type'),)``.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', on_delete=models.CASCADE)
    carrier_number = models.IntegerField()
    carrier_type = models.ForeignKey('controlled_list.CarrierType', on_delete=models.PROTECT)

    class Meta:
        db_table = 'isad_carriers'
        unique_together = (('isad', 'carrier_type'),)


class IsadRelatedFindingAids(models.Model):
    """
    Stores related finding aids information for an ISAD record.

    This model captures optional descriptive information and an optional URL to
    related finding aids resources.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', models.CASCADE)
    info = models.CharField(max_length=200, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'isad_related_finding_aids'


class IsadLocationOfOriginals(models.Model):
    """
    Stores location information for originals related to an ISAD record.

    This model captures an optional short description and an optional URL that
    indicates where originals may be found.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', models.CASCADE)
    info = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'isad_location_of_originals'


class IsadLocationOfCopies(models.Model):
    """
    Stores location information for copies related to an ISAD record.

    This model captures an optional short description and an optional URL that
    indicates where copies may be found.
    """

    id = models.AutoField(primary_key=True)
    isad = models.ForeignKey('Isad', models.CASCADE)
    info = models.CharField(max_length=100, blank=True, null=True)
    url = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'isad_location_of_copies'
