from django.db import models

from clockwork_api.mixins.detect_protected_mixin import DetectProtectedMixin
from finding_aids.models import FindingAidsEntity


class Container(models.Model, DetectProtectedMixin):
    id = models.AutoField(primary_key=True)

    archival_unit = models.ForeignKey('archival_unit.ArchivalUnit', on_delete=models.CASCADE)
    carrier_type = models.ForeignKey('controlled_list.CarrierType', on_delete=models.PROTECT)

    container_no = models.IntegerField()
    container_label = models.CharField(max_length=255, blank=True, null=True)

    permanent_id = models.CharField(max_length=50, blank=True, null=True)
    legacy_id = models.CharField(max_length=50, blank=True, null=True)
    barcode = models.CharField(max_length=30, blank=True, null=True, unique=True)
    old_id = models.IntegerField(blank=True, null=True)

    digital_version_exists = models.BooleanField(default=False)
    digital_version_creation_date = models.DateField(blank=True, null=True)
    digital_version_technical_metadata = models.TextField(blank=True, null=True)
    digital_version_online = models.BooleanField(default=False)
    
    user_created = models.CharField(max_length=100, blank=True)
    date_created = models.DateTimeField(blank=True, auto_now_add=True)

    user_updated = models.CharField(max_length=100, blank=True)
    date_updated = models.DateTimeField(blank=True, null=True, auto_now=True)

    def save(self, *args, **kwargs):
        if self.pk is None:
            container = Container.objects.filter(archival_unit=self.archival_unit).reverse().first()
            if container:
                self.container_no = container.container_no + 1
            else:
                self.container_no = 1
        super(Container, self).save()

    @property
    def has_digital_version(self):
        if self.digital_version_exists:
            return True
        if FindingAidsEntity.objects.filter(
                container=self,
                digital_version_exists=True).exists():
            return True
        return False

    class Meta:
        db_table = 'containers'
        unique_together = ('archival_unit', 'container_no')
