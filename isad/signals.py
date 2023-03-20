from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from isad.models import Isad
from isad.tasks import index_catalog_isad_record, index_catalog_isad_record_remove


@receiver(post_save, sender=Isad)
def update_isad_index(sender, instance, **kwargs):
    if instance.published:
        index_catalog_isad_record.delay(isad_id=instance.id)
    else:
        index_catalog_isad_record_remove.delay(isad_id=instance.id)


@receiver(pre_delete, sender=Isad)
def remove_isad_index(sender, instance, **kwargs):
    index_catalog_isad_record_remove.delay(isad_id=instance.id)
