from django.test import TestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import Building, CarrierType
from mlr.models import MLREntity, MLREntityLocation


class MLRModelTests(TestCase):
    fixtures = ['carrier_types', 'buildings']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=1100, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1100,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1100,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.carrier = CarrierType.objects.first()
        self.building = Building.objects.first()

    def test_count_size_and_locations(self):
        mlr = MLREntity.objects.create(series=self.series, carrier_type=self.carrier)
        Container.objects.create(archival_unit=self.series, carrier_type=self.carrier)
        Container.objects.create(archival_unit=self.series, carrier_type=self.carrier)

        MLREntityLocation.objects.create(
            mlr=mlr,
            building=self.building,
            module=1,
            row=2,
            section=3,
            shelf=4,
        )

        self.assertEqual(mlr.get_count(), 2)
        self.assertEqual(mlr.get_size(), 2 * self.carrier.width / 1000.0)
        self.assertEqual(mlr.get_locations(), f'1/2/3/4 ({self.building.building})')

    def test_locations_format_with_missing_values(self):
        mlr = MLREntity.objects.create(series=self.series, carrier_type=self.carrier)
        MLREntityLocation.objects.create(mlr=mlr)
        self.assertEqual(mlr.get_locations(), '-/-/-/- ()')
