from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from finding_aids.models import FindingAidsEntity
from finding_aids.tasks import index_catalog_finding_aids_entity, index_catalog_finding_aids_entity_remove


@receiver(post_save, sender=FindingAidsEntity)
def update_finding_aids_index(sender, instance, **kwargs):
    if instance.published:
        index_catalog_finding_aids_entity.delay(finding_aids_entity_id=instance.id)
    else:
        index_catalog_finding_aids_entity_remove.delay(finding_aids_entity_id=instance.id)


@receiver(pre_delete, sender=FindingAidsEntity)
def remove_finding_aids_index(sender, instance, **kwargs):
    index_catalog_finding_aids_entity_remove.delay(finding_aids_entity_id=instance.id)


@receiver(post_save, sender=FindingAidsEntity)
def track_save(sender, instance, **kwargs):
    print('a')