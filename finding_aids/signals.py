from django.db.models.signals import post_save, pre_delete
from django.db import transaction
from django.dispatch import receiver
from finding_aids.models import FindingAidsEntity
from finding_aids.tasks import (
    index_catalog_finding_aids_entity,
    index_catalog_finding_aids_entity_remove,
    index_meilisearch_finding_aids_entity,
    index_meilisearch_finding_aids_entity_remove,
)


def _delay_after_commit(task, **kwargs):
    transaction.on_commit(lambda: task.delay(**kwargs))


@receiver(post_save, sender=FindingAidsEntity)
def update_finding_aids_index(sender, instance, **kwargs):
    """
    Updates the search index when a finding aids entity is saved.

    Behavior depends on publication state:
        - If the entity is published, it is indexed
        - If the entity is unpublished, it is removed from the index
        - If the entity is marked as missing, it is removed from the index

    Indexing is performed asynchronously via Celery tasks.
    """
    if instance.published:
        if instance.missing:
            _delay_after_commit(
                index_catalog_finding_aids_entity_remove,
                finding_aids_entity_id=instance.id,
                document_id=instance.catalog_id,
            )
        else:
            _delay_after_commit(index_catalog_finding_aids_entity, finding_aids_entity_id=instance.id)
    else:
        _delay_after_commit(
            index_catalog_finding_aids_entity_remove,
            finding_aids_entity_id=instance.id,
            document_id=instance.catalog_id,
        )

    # Internal AMS search index should always contain saved records,
    # regardless of publication status.
    _delay_after_commit(index_meilisearch_finding_aids_entity, finding_aids_entity_id=instance.id)


@receiver(pre_delete, sender=FindingAidsEntity)
def remove_finding_aids_index(sender, instance, **kwargs):
    """
    Removes the finding aids entity from the search index before deletion.

    This ensures the index remains consistent even if the entity is deleted
    directly rather than unpublished first.
    """
    _delay_after_commit(
        index_catalog_finding_aids_entity_remove,
        finding_aids_entity_id=instance.id,
        document_id=instance.catalog_id,
    )
    _delay_after_commit(
        index_meilisearch_finding_aids_entity_remove,
        finding_aids_entity_id=instance.id,
        document_id=instance.catalog_id,
    )
