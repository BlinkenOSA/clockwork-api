from __future__ import unicode_literals

import uuid as uuid
from typing import Optional

from django.db import models
from django_date_extensions.fields import ApproximateDateField

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class Accession(models.Model, DetectProtectedMixin):
    """
    Represents a single accession record for materials received by the archive.

    This model stores metadata describing the accession, including its title,
    source (donor), physical storage location, approximate creation dates,
    custody information, and copyright status. The model also includes fields
    for staff workflow such as created/updated/approved user and timestamps.

    Attributes:
        id (int): Primary key.
        uuid (UUID): A generated unique identifier for external reference.
        seq (str | None): A generated sequence number in the form of year/seq (1995/001).
            Seq always restarts at 001 each year.

        title (str): Descriptive title for the accession.
        transfer_date (ApproximateDateField): Approximate date the material
            was transferred to the archive.
        method (AccessionMethod): Method of accessioning.
        description (str | None): Additional description.

        access_note (str | None): Notes on access restrictions.
        building (Building | None): Building where the accession is stored.
        module (int | None): Storage module number.
        row (int | None): Storage row number.
        section (int | None): Storage section number.
        shelf (int | None): Storage shelf number.

        archival_unit (ArchivalUnit | None): Related Archival Unit.
        archival_unit_legacy_number (int | None): Legacy Archival Unit identifier (from an older database - read-only).
        archival_unit_legacy_name (str | None): Legacy Archival Unit name (from an older database - read-only).

        donor (Donor): Donor providing the accession.
        creation_date_from (ApproximateDateField | None): Earliest creation date.
        creation_date_to (ApproximateDateField | None): Latest creation date.
        custodial_history (str | None): Description of prior custody.

        copyright_status (AccessionCopyrightStatus | None): Rights status.
        copyright_note (str | None): Additional copyright notes.
        note (str | None): Internal notes.

        user_created (str): Username of creator.
        date_created (datetime): Creation timestamp.
        user_updated (str): Username of last editor.
        date_updated (datetime | None): Last update timestamp.
        user_approved (str): Username of approver.
        date_approved (datetime | None): Approval timestamp.
    """
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    seq = models.CharField(unique=True, max_length=10, blank=True, null=True)

    title = models.CharField(max_length=300)
    transfer_date = ApproximateDateField()
    method = models.ForeignKey('AccessionMethod', on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)

    access_note = models.TextField(blank=True, null=True)
    building = models.ForeignKey('controlled_list.Building', on_delete=models.PROTECT, blank=True, null=True)
    module = models.IntegerField(blank=False, null=True)
    row = models.IntegerField(blank=False, null=True)
    section = models.IntegerField(blank=False, null=True)
    shelf = models.IntegerField(blank=False, null=True)

    archival_unit = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.PROTECT, blank=True, null=True)
    archival_unit_legacy_number = models.IntegerField(blank=True, null=True)
    archival_unit_legacy_name = models.CharField(max_length=300, blank=True, null=True)

    donor = models.ForeignKey('donor.Donor', on_delete=models.PROTECT)
    creation_date_from = ApproximateDateField(blank=True, null=True)
    creation_date_to = ApproximateDateField(blank=True, null=True)
    custodial_history = models.TextField(blank=True, null=True)
    copyright_status = models.ForeignKey('AccessionCopyrightStatus', on_delete=models.PROTECT, blank=True, null=True)
    copyright_note = models.TextField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    user_approved = models.CharField(max_length=100, blank=True)
    date_approved = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'accession_records'


class AccessionItem(models.Model):
    """
    Represents a single item within an accession, such as a container,
    box, folder, or group of materials.

    Attributes:
        id (int): Primary key.
        accession (Accession): Parent accession record.
        quantity (int): Number of units of this item. Example: 3
        container (str): Description of the container. Example: boxes
        content (str | None): Optional content description. Example: Written documentation accompanying the videos
    """
    id = models.AutoField(primary_key=True)
    accession = models.ForeignKey('Accession', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    container = models.CharField(max_length=100)
    content = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'accession_items'


class AccessionMethod(models.Model):
    """
    Represents the method or reason for accessioning material.
    Example values: Deposit, Donation, OSA Capture, OSA Purchase

    Attributes:
        id (int): Primary key.
        method (str): Unique description of the accession method.
    """
    id = models.AutoField(primary_key=True)
    method = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'accession_methods'
        ordering = ['method']


class AccessionCopyrightStatus(models.Model):
    """
    Represents the copyright status assigned to an accession.
    Example values: Copyright held by creator, Copyright held by OSA, Public Domain, Orphan Work

    Attributes:
        id (int): Primary key.
        status (str): Unique label describing copyright status.
    """
    id = models.AutoField(primary_key=True)
    status = models.CharField(unique=True, max_length=200)

    class Meta:
        db_table = 'accession_copyright_statuses'
        ordering = ['status']
