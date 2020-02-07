from __future__ import unicode_literals

import uuid as uuid
from django.db import models
from django_date_extensions.fields import ApproximateDateField

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin


class Accession(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    seq = models.CharField(unique=True, max_length=10, blank=True, null=True)

    title = models.CharField(max_length=300)
    transfer_date = ApproximateDateField()
    method = models.ForeignKey('AccessionMethod', on_delete=models.PROTECT)
    description = models.TextField(blank=True, null=True)

    access_note = models.TextField(blank=True, null=True)
    building = models.ForeignKey('controlled_list.Building', on_delete=models.PROTECT, blank=True, null=True)
    module = models.IntegerField(blank=True, null=True)
    row = models.IntegerField(blank=True, null=True)
    section = models.IntegerField(blank=True, null=True)
    shelf = models.IntegerField(blank=True, null=True)

    archival_unit = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.PROTECT, blank=True, null=True)
    archival_unit_legacy_number = models.IntegerField(blank=True, null=True)
    archival_unit_legacy_name = models.CharField(max_length=300, blank=True, null=True)

    donor = models.ForeignKey('donor.Donor', on_delete=models.PROTECT)
    creation_date_from = ApproximateDateField(blank=True)
    creation_date_to = ApproximateDateField(blank=True)
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
    id = models.AutoField(primary_key=True)
    accession = models.ForeignKey('Accession', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    container = models.CharField(max_length=100)
    content = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'accession_items'


class AccessionMethod(models.Model):
    id = models.AutoField(primary_key=True)
    method = models.CharField(unique=True, max_length=100)

    class Meta:
        db_table = 'accession_methods'
        ordering = ['method']


class AccessionCopyrightStatus(models.Model):
    id = models.AutoField(primary_key=True)
    status = models.CharField(unique=True, max_length=200)

    class Meta:
        db_table = 'accession_copyright_statuses'
        ordering = ['status']
