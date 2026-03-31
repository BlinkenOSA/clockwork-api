from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import Building, CarrierType
from mlr.models import MLREntity, MLREntityLocation


class MLRViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types', 'buildings']

    def setUp(self):
        super().setUp()
        fonds = ArchivalUnit.objects.create(fonds=1101, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1101,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1101,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.carrier = CarrierType.objects.first()
        self.building = Building.objects.first()

        self.mlr = MLREntity.objects.create(series=self.series, carrier_type=self.carrier, notes='Note')
        MLREntityLocation.objects.create(
            mlr=self.mlr,
            building=self.building,
            module=1,
            row=2,
            section=3,
            shelf=4,
        )
        Container.objects.create(archival_unit=self.series, carrier_type=self.carrier)

    def test_list_returns_computed_fields(self):
        response = self.client.get(reverse('mlr-v1:mlr-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        row = response.data['results'][0]
        self.assertEqual(row['quantity'], 1)
        self.assertEqual(row['carrier_type'], self.carrier.type)
        self.assertIn('mrss', row)

    def test_list_filters(self):
        response = self.client.get(
            reverse('mlr-v1:mlr-list'),
            {'fonds': self.series.id, 'carrier_type': self.carrier.id, 'building': self.building.id},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)

    def test_detail_endpoint(self):
        response = self.client.get(reverse('mlr-v1:mlr-detail', kwargs={'pk': self.mlr.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['series'], self.series.id)
        self.assertEqual(len(response.data['locations']), 1)

    def test_export_csv(self):
        response = self.client.get(reverse('mlr-v1:mlr-export-csv'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('series;carrier;locations', response.content.decode('utf-8'))
