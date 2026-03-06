from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType


class DashboardStatisticsViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        self.init()
        self.fonds = ArchivalUnit.objects.create(
            fonds=400,
            level='F',
            title='Test Fonds'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=400,
            subfonds=1,
            level='SF',
            title='Test Subfonds',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=400,
            subfonds=1,
            series=1,
            level='S',
            title='Test Series',
            parent=self.subfonds
        )

        self.carrier_type = CarrierType.objects.first()
        Container.objects.create(archival_unit=self.series, carrier_type=self.carrier_type)
        Container.objects.create(archival_unit=self.series, carrier_type=self.carrier_type)

    def test_linear_meter_endpoint_returns_dataset(self):
        response = self.client.get(
            reverse('dashboard-v1:linear-meter', kwargs={'archival_unit': self.series.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('linear_meter', response.data)
        self.assertIn('linear_meter_percentage', response.data)
        self.assertIn('linear_meter_all', response.data)
        self.assertIn('linear_meter_all_pecentage', response.data)

    def test_carrier_types_endpoint_returns_distribution(self):
        response = self.client.get(
            reverse('dashboard-v1:carrier-types', kwargs={'archival_unit': self.series.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['type'], self.carrier_type.type)
        self.assertEqual(response.data[0]['total'], 2)

    def test_published_items_endpoint_with_no_items(self):
        qs = Mock()
        qs.count.return_value = 0

        with patch('dashboard.views.statistics_views.FindingAidsEntity.objects.filter', return_value=qs):
            response = self.client.get(
                reverse('dashboard-v1:folders-items', kwargs={'archival_unit': self.series.id})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_items'], 0)
        self.assertEqual(response.data['published_items'], 0)
        self.assertEqual(response.data['published_items_percentage'], '0.00')
