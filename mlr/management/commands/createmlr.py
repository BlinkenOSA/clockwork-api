from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from mlr.models import MLREntity


class Command(BaseCommand):
    help = 'Creates the MLR records based on the existing ones.'

    def handle(self, *args, **options):
        containers = Container.objects.values('archival_unit', 'carrier_type').distinct()

        for container in containers:
            archival_unit = ArchivalUnit.objects.get(pk=container['archival_unit'])
            carrier_type = CarrierType.objects.get(pk=container['carrier_type'])
            MLREntity.objects.get_or_create(series=archival_unit, carrier_type=carrier_type)
