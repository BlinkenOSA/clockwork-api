from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from dashboard.views.search_views import DashboardSearchView


class DashboardMeilisearchConfigurationTests(SimpleTestCase):
    @override_settings(
        MEILISEARCH_URL="http://meilisearch.test:7700",
        MEILISEARCH_DASHBOARD_SEARCH_INDEX="old-dashboard-index",
        MEILISEARCH_AMS_API_KEY="ams-key",
        MEILISEARCH_AMS_INDEX="ams-index",
        MEILISEARCH_CATALOG_API_KEY="catalog-key",
        MEILISEARCH_CATALOG_INDEX="catalog-test-index",
    )
    @patch("dashboard.views.search_views.meilisearch.Client")
    def test_dashboard_reads_from_ams_destination(self, client_class):
        index = DashboardSearchView()._get_index()

        client_class.assert_called_once_with("http://meilisearch.test:7700", "ams-key")
        client_class.return_value.index.assert_called_once_with("ams-index")
        self.assertIs(index, client_class.return_value.index.return_value)
