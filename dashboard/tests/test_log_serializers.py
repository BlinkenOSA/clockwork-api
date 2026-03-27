import datetime

from django.test import TestCase
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types
from dashboard.serializers.log_serializers import DigitizationLogSerializer
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class DigitizationLogSerializerTests(TestCase):
    def setUp(self):
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types()
        self.container = make_container(self.series, self.carrier_type)

    def test_container_no_format(self):
        data = DigitizationLogSerializer(self.container).data
        self.assertEqual(data['container_no'], 'HU OSA 206-3-1:1')


class DashboardLogViewsTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types()
        self.container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            digital_version_exists=True,
            digital_version_creation_date=datetime.date.today(),
        )

    def test_digitization_log_endpoint(self):
        response = self.client.get(reverse('dashboard-v1:digitization-log'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertIn('container_no', response.data[0])
