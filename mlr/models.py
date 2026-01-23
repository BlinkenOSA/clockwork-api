# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from container.models import Container


class MLREntity(models.Model):
    """
    Core model representing a Master Location Register (MLR) entry.

    An MLR entry ties an archival series (:class:`archival_unit.ArchivalUnit`)
    to a carrier type (:class:`controlled_list.CarrierType`) and provides
    derived helpers for calculating:
        - container count for the series/carrier type pair
        - estimated physical size (using carrier width)
        - a human-readable list of associated storage locations

    Related locations are stored via :class:`MLREntityLocation` using the
    ``locations`` related name.
    """

    id = models.AutoField(primary_key=True)
    series = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.CASCADE)
    carrier_type = models.ForeignKey('controlled_list.CarrierType', on_delete=models.CASCADE)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'mlr_records'

    def get_count(self):
        """
        Returns the number of containers matching this MLR entry.

        The count is computed by querying :class:`container.models.Container`
        for containers with the same archival unit (series) and carrier type.

        Returns
        -------
        int
            Number of matching containers.
        """
        return Container.objects.filter(archival_unit=self.series, carrier_type=self.carrier_type).count()

    def get_size(self):
        """
        Returns the estimated physical size of the entry in linear meters.

        The size is computed as::

            container_count * carrier_type.width / 1000.0

        where ``width`` is assumed to be expressed in millimeters.

        Returns
        -------
        float
            Estimated size in linear meters.
        """
        return self.get_count() * self.carrier_type.width / 1000.0

    def get_locations(self):
        """
        Returns a human-readable string of all associated locations.

        Each location is formatted as ``module/row/section/shelf (building)``,
        with missing numeric components rendered as ``'-'``.

        Returns
        -------
        str
            Semicolon-separated list of formatted location strings.
        """
        loc = []
        for l in self.locations.all():
            m = str(l.module) if l.module else "-"
            r = str(l.row) if l.row else "-"
            s = str(l.section) if l.section else "-"
            sh = str(l.shelf) if l.shelf else "-"
            loc.append("%s/%s/%s/%s (%s)" % (m, r, s, sh, l.building.building if l.building else ''))
        return "; ".join(loc)


class MLREntityLocation(models.Model):
    """
    Location entry associated with a Master Location Register (MLR) record.

    Each location stores optional shelf address components (module, row,
    section, shelf) and an optional building reference. Multiple locations can
    be associated with a single :class:`MLREntity` via the ``locations`` related
    name.
    """

    id = models.AutoField(primary_key=True)
    mlr = models.ForeignKey('mlr.MLREntity', on_delete=models.CASCADE, related_name='locations')

    building = models.ForeignKey('controlled_list.Building', on_delete=models.PROTECT, blank=True, null=True)
    module = models.IntegerField(blank=True, null=True)
    row = models.IntegerField(blank=True, null=True)
    section = models.IntegerField(blank=True, null=True)
    shelf = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'mlr_record_locations'
