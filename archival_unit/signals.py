from django.db.models.signals import post_save
from django.dispatch import receiver

from archival_unit.models import ArchivalUnit
from isad.tasks import index_catalog_isad_record, index_catalog_isad_record_remove


@receiver(post_save, sender=ArchivalUnit)
def update_isad_when_archival_unit_saved(sender, instance, **kwargs):
    if hasattr(instance, 'isad'):
        if instance.isad.published:
            index_catalog_isad_record.delay(isad_id=instance.isad.id)
        else:
            index_catalog_isad_record_remove.delay(isad_id=instance.isad.id)
