from django.db.models.signals import post_save
from django.dispatch import receiver

from container.models import Container
from finding_aids.models import FindingAidsEntity
from finding_aids.tasks import index_catalog_finding_aids_entity, index_catalog_finding_aids_entity_remove


@receiver(post_save, sender=Container)
def update_finding_aids_index_upon_container_save(sender, instance, **kwargs):
    """
    Updates the finding-aids search index when a container is saved.

    Any change to a container may affect the visibility or metadata of its
    associated finding-aid entities. This signal ensures that all related
    finding aids are re-indexed appropriately.

    Resolution behavior:
        - Published finding-aid entities are indexed
        - Unpublished finding-aid entities are removed from the index

    Indexing is performed asynchronously via background tasks.
    """
    finding_aids_entities = FindingAidsEntity.objects.filter(container=instance)

    # Index the underlying finding aids entities
    for finding_aids_entity in finding_aids_entities.all():
        if finding_aids_entity.published:
            index_catalog_finding_aids_entity.delay(finding_aids_entity_id=finding_aids_entity.id)
        else:
            index_catalog_finding_aids_entity_remove.delay(finding_aids_entity_id=finding_aids_entity.id)
