from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver

from container.models import Container
from mlr.models import MLREntity


@receiver(post_delete, sender=Container)
def downsync_mlr(sender, instance, **kwargs):
    """
    Synchronizes the Master Location Register after a container is deleted.

    This signal handler reacts to ``post_delete`` events on
    :class:`container.models.Container`. If the deleted container was the last
    container for a given archival unit (series) and carrier type combination,
    the corresponding :class:`mlr.models.MLREntity` record is removed.

    Notes
    -----
    This ensures that MLR entries exist only when at least one container
    references the given (series, carrier_type) pair.
    """
    carrier_type = instance.carrier_type
    archival_unit = instance.archival_unit
    if Container.objects.filter(archival_unit=archival_unit, carrier_type=carrier_type).count() == 0:
        MLREntity.objects.get(series=archival_unit, carrier_type=carrier_type).delete()


@receiver(pre_save, sender=Container)
def check_empty_mlr(sender, instance, *args, **kwargs):
    """
    Removes MLR entries when a container update would leave them empty.

    This signal handler reacts to ``pre_save`` events on
    :class:`container.models.Container`. When updating an existing container,
    it checks whether the container being modified is the last one associated
    with its previous (archival_unit, carrier_type) pair. If so, the
    corresponding :class:`mlr.models.MLREntity` entry is deleted.

    Notes
    -----
    This handles cases where a container changes archival unit or carrier type,
    preventing stale MLR records from persisting after the update.
    """
    if instance.pk and Container.objects.filter(id=instance.pk).exists():
        previous_container = Container.objects.get(id=instance.pk)
        carrier_type = previous_container.carrier_type
        archival_unit = previous_container.archival_unit
        container_count = Container.objects.filter(archival_unit=archival_unit, carrier_type=carrier_type).count()
        if container_count == 1:
            MLREntity.objects.filter(series=archival_unit, carrier_type=carrier_type).delete()


@receiver(post_save, sender=Container)
def upsync_mlr(sender, instance, **kwargs):
    """
    Synchronizes the Master Location Register after a container is saved.

    This signal handler reacts to ``post_save`` events on
    :class:`container.models.Container` and ensures that a corresponding
    :class:`mlr.models.MLREntity` exists for the container's
    (archival_unit, carrier_type) pair.

    Notes
    -----
    If the MLR entry already exists, it is left unchanged. Otherwise, a new
    entry is created.
    """
    carrier_type = instance.carrier_type
    archival_unit = instance.archival_unit
    MLREntity.objects.get_or_create(series=archival_unit, carrier_type=carrier_type)
