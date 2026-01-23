from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

from isad.models import Isad
from isad.tasks import index_catalog_isad_record, index_catalog_isad_record_remove


@receiver(post_save, sender=Isad)
def update_isad_index(sender, instance, **kwargs):
    """
    Updates the catalog search index after an ISAD record is saved.

    This signal handler reacts to ``post_save`` events on :class:`isad.models.Isad`.
    Depending on the publication state of the record, it either indexes or
    removes the record from the catalog search index.

    Behavior
    --------
    - If ``instance.published`` is True:
        Triggers an asynchronous task to index the ISAD record.
    - If ``instance.published`` is False:
        Triggers an asynchronous task to remove the ISAD record from the index.

    Notes
    -----
    Indexing operations are delegated to background tasks to avoid blocking
    the request/response cycle.
    """
    if instance.published:
        index_catalog_isad_record.delay(isad_id=instance.id)
    else:
        index_catalog_isad_record_remove.delay(isad_id=instance.id)


@receiver(pre_delete, sender=Isad)
def remove_isad_index(sender, instance, **kwargs):
    """
    Removes the ISAD record from the catalog search index before deletion.

    This signal handler reacts to ``pre_delete`` events on
    :class:`isad.models.Isad` and ensures that the corresponding catalog index
    entry is removed before the database record is deleted.

    Notes
    -----
    The removal is executed asynchronously via a background task.
    """
    index_catalog_isad_record_remove.delay(isad_id=instance.id)
