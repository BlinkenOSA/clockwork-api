# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models


# Create your models here.
class DigitalVersion(models.Model):
    id = models.AutoField(primary_key=True)
    finding_aids_entity = models.ForeignKey('finding_aids.FindingAidsEntity', blank=True, null=True, on_delete=models.CASCADE)
    container = models.ForeignKey('container.Container', blank=True, null=True, on_delete=models.CASCADE)

    identifier = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    level = models.CharField(max_length=1, choices=(('M', 'Master'), ('A', 'Access Copy')), db_index=True, default='A')

    digital_collection = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    filename = models.CharField(max_length=200, blank=True, null=True, db_index=True)

    label = models.CharField(max_length=50, blank=True, null=True)

    available_research_cloud = models.BooleanField(default=False, db_index=True)
    available_online = models.BooleanField(default=False, db_index=True)

    technical_metadata = models.TextField(blank=True, null=True)
    research_cloud_path = models.TextField(blank=True, null=True)

    creation_date = models.DateField(blank=True, null=True, auto_now_add=True)

    class Meta:
        db_table = 'digital_versions'


class DigitalVersionPhysicalCopy(models.Model):
    id = models.AutoField(primary_key=True)
    digital_version = models.ForeignKey('DigitalVersion', on_delete=models.CASCADE)
    storage_unit = models.CharField(max_length=50, blank=True, null=True)
    storage_unit_label = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        db_table = 'digital_version_physical_copies'
