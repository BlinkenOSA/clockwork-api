from typing import Type, Any

from django.db.models.signals import post_save
from django.dispatch import receiver

from archival_unit.models import ArchivalUnit
from isad.tasks import index_catalog_isad_record, index_catalog_isad_record_remove


@receiver(post_save, sender=ArchivalUnit)
def update_isad_when_archival_unit_saved(
        sender: Type[ArchivalUnit],
        instance: ArchivalUnit,
        **kwargs: Any
) -> None:
    """
    Updates the index of the related ISAD record whenever an ArchivalUnit is saved.

    Behavior:
        - If the archival unit has an associated ISAD record (reverse OneToOne)
        - AND the ISAD record is published → reindex the record.
        - If the ISAD record exists but is not published → remove it from the index.

    This allows the ISAD search index to remain in sync with archival unit updates,
    without requiring manual re-indexing.

    Args:
        sender: The model class that triggered the signal (ArchivalUnit).
        instance: The specific archival unit instance that was saved.
        **kwargs: Additional signal metadata (ignored).
    """
    if hasattr(instance, 'isad'):
        if instance.isad.published:
            # Reindex published records
            index_catalog_isad_record.delay(isad_id=instance.isad.id)
        else:
            # Remove unpublished or draft records from index
            index_catalog_isad_record_remove.delay(isad_id=instance.isad.id)
