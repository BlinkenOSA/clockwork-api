import datetime

from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from dashboard.serializers.log_serializers import DigitizationLogSerializer
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class DigitizationLogSerializerTests(TestCase):
    fixtures = ['carrier_types']

    def test_container_no_format(self):
        fonds = ArchivalUnit.objects.create(fonds=500, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=500,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        series = ArchivalUnit.objects.create(
            fonds=500,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        container = Container.objects.create(
            archival_unit=series,
            carrier_type=CarrierType.objects.first(),
        )

        data = DigitizationLogSerializer(container).data
        self.assertEqual(data['container_no'], 'HU OSA 500-1-1:1')


class DashboardLogViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        self.init()
        fonds = ArchivalUnit.objects.create(fonds=600, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=600,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        series = ArchivalUnit.objects.create(
            fonds=600,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        Container.objects.create(
            archival_unit=series,
            carrier_type=CarrierType.objects.first(),
            digital_version_exists=True,
            digital_version_creation_date=datetime.date.today(),
        )

    def test_digitization_log_endpoint(self):
        response = self.client.get(reverse('dashboard-v1:digitization-log'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('container_no', response.data[0])
