from rest_framework import status
from rest_framework.reverse import reverse

from accession.tests.helpers import make_accession_method, make_accession
from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from container.tests.helpers import make_container
from controlled_list.models import CarrierType
from controlled_list.tests.helpers import make_carrier_types
from donor.tests.helpers import make_donor


class DashboardAnalyticsViewTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()

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
        super().setUp()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types()
        self.container = make_container(self.series, self.carrier_type)

        self.method = make_accession_method()
        self.donor = make_donor()

        self.accession = make_accession(
            fonds=self.fonds,
            method=self.method,
            donor=self.donor
        )

    def test_accession_log_endpoint(self):
        response = self.client.get(reverse("dashboard-v1:accession-log"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_digitization_log_endpoint(self):
        make_container(self.series, self.carrier_type, digital_version_exists=True)
        response = self.client.get(reverse("dashboard-v1:digitization-log"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
