from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class DashboardAnalyticsViewsTests(TestViewsBaseClass):
    def test_activity_endpoint_returns_monthly_rows(self):
        with patch('dashboard.views.analytics_views.Accession.objects.filter') as accession_filter, \
             patch('dashboard.views.analytics_views.Isad.objects.filter') as isad_filter, \
             patch('dashboard.views.analytics_views.Isaar.objects.filter') as isaar_filter, \
             patch('dashboard.views.analytics_views.FindingAidsEntity.objects.filter') as fa_filter:
            accession_filter.return_value.count.return_value = 0
            isad_filter.return_value.count.return_value = 0
            isaar_filter.return_value.count.return_value = 0
            fa_filter.return_value.count.return_value = 0

            response = self.client.get(reverse('dashboard-v1:analytics-activity-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(len(response.data) % 4, 0)
        self.assertEqual({'month', 'type', 'value'}, set(response.data[0].keys()))

    def test_totals_endpoint_returns_monthly_rows(self):
        with patch('dashboard.views.analytics_views.Accession.objects.filter') as accession_filter, \
             patch('dashboard.views.analytics_views.Isad.objects.filter') as isad_filter, \
             patch('dashboard.views.analytics_views.Isaar.objects.filter') as isaar_filter, \
             patch('dashboard.views.analytics_views.FindingAidsEntity.objects.filter') as fa_filter:
            accession_filter.return_value.count.return_value = 1
            isad_filter.return_value.count.return_value = 2
            isaar_filter.return_value.count.return_value = 3
            fa_filter.return_value.count.return_value = 4

            response = self.client.get(reverse('dashboard-v1:analytics-totals-view'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(len(response.data) % 4, 0)
        self.assertEqual({'month', 'type', 'value'}, set(response.data[0].keys()))
