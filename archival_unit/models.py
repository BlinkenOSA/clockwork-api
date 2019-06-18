import uuid as uuid
from django.db import models
from django.utils import timezone


class ArchivalUnit(models.Model):
    id = models.AutoField(primary_key=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    parent = models.ForeignKey('self', null=True, blank=True, related_name='children',
                               db_index=True, on_delete=models.PROTECT)
    theme = models.ManyToManyField('controlled_list.ArchivalUnitTheme', blank=True)

    fonds = models.IntegerField()
    subfonds = models.IntegerField(default=0)
    series = models.IntegerField(default=0)

    sort = models.CharField(max_length=12, blank=True)

    title = models.CharField(max_length=500, blank=True, null=True)
    title_full = models.CharField(max_length=2000, blank=True, null=True)
    title_original = models.CharField(max_length=500, blank=True, null=True)
    original_locale = models.ForeignKey('controlled_list.Locale', blank=True, null=True, on_delete=models.PROTECT)

    acronym = models.CharField(max_length=50, blank=True, null=True)
    reference_code = models.CharField(max_length=20)
    reference_code_id = models.CharField(max_length=20)

    level = models.CharField(max_length=2)
    status = models.CharField(max_length=10, default='Final')
    ready_to_publish = models.BooleanField(default=False)

    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def get_fonds(self):
        if self.level == 'F':
            return self
        elif self.level == 'SF':
            return self.parent
        else:
            return self.parent.parent

    def get_subfonds(self):
        if self.level == 'F':
            return None
        elif self.level == 'SF':
            return self
        else:
            return self.parent

    def set_sort(self):
        self.sort = '%04d%04d%04d' % (self.fonds, self.subfonds, self.series)

    def set_title_full(self):
        if self.level == 'F':
            self.title_full = self.reference_code + ' ' + self.title
        elif self.level == 'SF':
            fonds_title = self.parent.title
            if self.subfonds == 0:
                self.title_full = self.reference_code + ' ' + fonds_title
            else:
                self.title_full = self.reference_code + ' ' + fonds_title + ': ' + self.title
        else:
            subfonds_title = self.parent.title
            fonds_title = self.parent.parent.title
            if self.level == 'S' and self.subfonds == 0:
                self.title_full = self.reference_code + ' ' + fonds_title + ': ' + self.title
            else:
                self.title_full = self.reference_code + ' ' + fonds_title + ': ' + subfonds_title + ': ' + self.title

    def set_reference_code(self):
        if self.level == 'F':
            self.reference_code = 'HU OSA ' + str(self.fonds)
            self.reference_code_id = 'hu_osa_' + str(self.fonds)
        elif self.level == 'SF':
            self.reference_code = 'HU OSA ' + str(self.fonds) + '-' + str(self.subfonds)
            self.reference_code_id = 'hu_osa_' + str(self.fonds) + '-' + str(self.subfonds)
        else:
            self.reference_code = 'HU OSA ' + str(self.fonds) + '-' + str(self.subfonds) + '-' + str(self.series)
            self.reference_code_id = 'hu_osa_' + str(self.fonds) + '-' + str(self.subfonds) + '-' + str(self.series)

    def save(self, **kwargs):
        self.set_sort()
        self.set_reference_code()
        self.set_title_full()
        super(ArchivalUnit, self).save()

    class Meta:
        db_table = 'archival_units'
        ordering = ['fonds', 'subfonds', 'series']
        unique_together = (("fonds", "subfonds", "series", "level"),)
