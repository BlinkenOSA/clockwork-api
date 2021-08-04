from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver

from container.models import Container
from mlr.models import MLREntity


@receiver(post_delete, sender=Container)
def downsync_mlr(sender, **kwargs):
    carrier_type = kwargs['instance'].carrier_type
    archival_unit = kwargs['instance'].archival_unit
    if Container.objects.filter(archival_unit=archival_unit, carrier_type=carrier_type).count() == 0:
        MLREntity.objects.get(series=archival_unit, carrier_type=carrier_type).delete()


@receiver(pre_save, sender=Container)
def upsync_mlr(sender, **kwargs):
    carrier_type = kwargs['instance'].carrier_type
    archival_unit = kwargs['instance'].archival_unit
    MLREntity.objects.get_or_create(series=archival_unit, carrier_type=carrier_type)


