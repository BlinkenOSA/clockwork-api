from rest_framework import status
from rest_framework.reverse import reverse

from accession.models import Accession, AccessionMethod
from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType
from donor.models import Donor
from authority.models import Country


class DashboardAnalyticsViewTests(TestViewsBaseClass):
    def setUp(self):
        self.init()

    def test_activity_analytics_shape(self):
        response = self.client.get(reverse("dashboard-v1:analytics-activity-view"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data) % 4, 0)
        self.assertTrue(all("month" in r and "type" in r and "value" in r for r in response.data))

    def test_totals_analytics_shape(self):
        response = self.client.get(reverse("dashboard-v1:analytics-totals-view"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data) % 4, 0)
        self.assertTrue(all("month" in r and "type" in r and "value" in r for r in response.data))


class DashboardLogViewTests(TestViewsBaseClass):
    def setUp(self):
        self.init()
        self.fonds = ArchivalUnit.objects.create(
            fonds=200,
            level='F',
            title='Dashboard Fonds'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=200,
            subfonds=1,
            level='SF',
            title='Dashboard Subfonds',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=200,
            subfonds=1,
            series=1,
            level='S',
            title='Dashboard Series',
            parent=self.subfonds
        )
        self.method = AccessionMethod.objects.create(method='Donation')
        self.country = Country.objects.create(alpha3='USA', country='United States')
        self.donor = Donor.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            postal_code='12345',
            country=self.country,
            city='NYC',
            address='1 Main St'
        )

    def test_accession_log_endpoint(self):
        Accession.objects.create(
            title='Test Accession',
            transfer_date='2020-01-01',
            method=self.method,
            donor=self.donor,
            archival_unit=self.fonds
        )
        response = self.client.get(reverse("dashboard-v1:accession-log"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_digitization_log_endpoint(self):
        carrier = CarrierType.objects.create(type='Box', width=10)
        Container.objects.create(
            archival_unit=self.series,
            carrier_type=carrier,
            container_no=1,
            digital_version_exists=True
        )
        response = self.client.get(reverse("dashboard-v1:digitization-log"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
