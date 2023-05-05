from django.db.models.signals import pre_save, post_delete, post_save
from django.dispatch import receiver

from container.models import Container
from mlr.models import MLREntity


@receiver(post_delete, sender=Container)
def downsync_mlr(sender, instance, **kwargs):
    carrier_type = instance.carrier_type
    archival_unit = instance.archival_unit
    if Container.objects.filter(archival_unit=archival_unit, carrier_type=carrier_type).count() == 0:
        MLREntity.objects.get(series=archival_unit, carrier_type=carrier_type).delete()


@receiver(pre_save, sender=Container)
def check_empty_mlr(sender, instance, *args, **kwargs):
    if instance.pk:
        previous_container = Container.objects.get(id=instance.pk)
        carrier_type = previous_container.carrier_type
        archival_unit = previous_container.archival_unit
        container_count = Container.objects.filter(archival_unit=archival_unit, carrier_type=carrier_type).count()
        if container_count == 1:
            MLREntity.objects.filter(series=archival_unit, carrier_type=carrier_type).delete()


@receiver(post_save, sender=Container)
def upsync_mlr(sender, instance, **kwargs):
    carrier_type = instance.carrier_type
    archival_unit = instance.archival_unit
    MLREntity.objects.get_or_create(series=archival_unit, carrier_type=carrier_type)


