# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from container.models import Container


class MLREntity(models.Model):
    id = models.AutoField(primary_key=True)
    series = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.CASCADE)
    carrier_type = models.ForeignKey('controlled_list.CarrierType', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'mlr_records'

    def get_count(self):
        return Container.objects.filter(archival_unit=self.series, carrier_type=self.carrier_type).count()

    def get_size(self):
        return self.get_count() * self.carrier_type.width / 1000.0

    def get_locations(self):
        loc = []
        for l in self.locations.all():
            m = str(l.module) if l.module else "-"
            r = str(l.row) if l.row else "-"
            s = str(l.section) if l.section else "-"
            sh = str(l.shelf) if l.shelf else "-"
            loc.append("%s/%s/%s/%s (%s)" % (m, r, s, sh, l.building.building))
        return "; ".join(loc)


class MLREntityLocation(models.Model):
    id = models.AutoField(primary_key=True)
    mlr = models.ForeignKey('mlr.MLREntity', on_delete=models.CASCADE, related_name='locations')

    building = models.ForeignKey('controlled_list.Building', on_delete=models.PROTECT, blank=True, null=True)
    module = models.IntegerField(blank=True, null=True)
    row = models.IntegerField(blank=True, null=True)
    section = models.IntegerField(blank=True, null=True)
    shelf = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'mlr_record_locations'
