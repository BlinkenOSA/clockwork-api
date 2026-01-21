from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from finding_aids.models import FindingAidsEntity
from finding_aids.tasks import index_catalog_finding_aids_entity, index_catalog_finding_aids_entity_remove


@receiver(post_save, sender=FindingAidsEntity)
def update_finding_aids_index(sender, instance, **kwargs):
    """
    Updates the search index when a finding aids entity is saved.

    Behavior depends on publication state:
        - If the entity is published, it is indexed
        - If the entity is unpublished, it is removed from the index

    Indexing is performed asynchronously via Celery tasks.
    """
    if instance.published:
        index_catalog_finding_aids_entity.delay(finding_aids_entity_id=instance.id)
    else:
        index_catalog_finding_aids_entity_remove.delay(finding_aids_entity_id=instance.id)


@receiver(pre_delete, sender=FindingAidsEntity)
def remove_finding_aids_index(sender, instance, **kwargs):
    """
    Removes the finding aids entity from the search index before deletion.

    This ensures the index remains consistent even if the entity is deleted
    directly rather than unpublished first.
    """
    index_catalog_finding_aids_entity_remove.delay(finding_aids_entity_id=instance.id)
