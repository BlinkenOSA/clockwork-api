from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class DashboardSearchViewTests(TestViewsBaseClass):
    def test_search_returns_empty_for_blank_query(self):
        response = self.client.get(reverse('dashboard-v1:search'), {'q': ''})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])

    @patch('dashboard.views.search_views.meilisearch.Client')
    def test_search_uses_meilisearch_and_normalizes_hits(self, client_class):
        fake_index = Mock()
        fake_index.search.return_value = {
            'estimatedTotalHits': 2,
            'hits': [
                {
                    'id': 'isad_1',
                    'record_type': 'isad',
                    'title': 'Open Society Archives Fonds',
                    'scope_and_content_abstract': 'ISAD abstract text',
                    'reference_code': 'HU OSA 300',
                    'ams_id': 10,
                },
                {
                    'id': 'fa_1',
                    'title': 'Folder 1',
                    'contents_summary': 'FA summary text',
                    'call_number': 'HU OSA 300-1-1:1/1',
                    'series_id': 99,
                    'guid': 'osa:abc',
                },
            ]
        }

        fake_client = Mock()
        fake_client.index.return_value = fake_index
        client_class.return_value = fake_client

        response = self.client.get(
            reverse('dashboard-v1:search'),
            {'q': 'osa', 'record_type': 'isad,finding_aids', 'limit': 10, 'offset': 5}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 2)
        self.assertEqual(len(response.data['results']), 2)
        self.assertEqual(response.data['results'][0]['record_type'], 'isad')
        self.assertEqual(response.data['results'][1]['record_type'], 'finding_aids_entity')

        fake_client.index.assert_called_once()
        fake_index.search.assert_called_once_with(
            'osa',
            {
                'limit': 10,
                'offset': 5,
                'filter': 'record_type IN ["isad", "finding_aids_entity"]'
            }
        )

    @patch('dashboard.views.search_views.meilisearch.Client')
    def test_search_limits_results_to_allowed_archival_units(self, client_class):
        fonds = make_fonds()
        subfonds = make_subfonds(fonds)
        allowed_series = make_series(subfonds)
        other_series = make_series(
            subfonds,
            uuid='98d10b78-aa2b-40e7-b647-b087f61c28ba',
            series=2,
            sort='020600030002',
            title='Other series',
            title_full='HU OSA 206-3-2 Other series',
            reference_code='HU OSA 206-3-2',
            reference_code_id='hu_osa_206-3-2',
        )
        self.user_profile.allowed_archival_units.add(allowed_series)

        fake_index = Mock()
        fake_index.search.return_value = {
            'estimatedTotalHits': 0,
            'hits': []
        }

        fake_client = Mock()
        fake_client.index.return_value = fake_index
        client_class.return_value = fake_client

        response = self.client.get(reverse('dashboard-v1:search'), {'q': 'osa'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fake_index.search.assert_called_once_with(
            'osa',
            {
                'limit': 20,
                'offset': 0,
                'filter': (
                    f'(archival_unit_id IN [{allowed_series.id}] OR '
                    f'series_id IN [{allowed_series.id}] OR '
                    f'(record_type = "isad" AND ams_id IN [{allowed_series.id}]) OR '
                    f'(record_type = "archival_unit" AND ams_id IN [{allowed_series.id}]))'
                )
            }
        )
        self.assertNotIn(str(other_series.id), fake_index.search.call_args.args[1]['filter'])

    @patch('dashboard.views.search_views.meilisearch.Client')
    def test_search_combines_record_type_and_allowed_archival_unit_filters(self, client_class):
        fonds = make_fonds()
        subfonds = make_subfonds(fonds)
        allowed_series = make_series(subfonds)
        self.user_profile.allowed_archival_units.add(allowed_series)

        fake_index = Mock()
        fake_index.search.return_value = {
            'estimatedTotalHits': 0,
            'hits': []
        }

        fake_client = Mock()
        fake_client.index.return_value = fake_index
        client_class.return_value = fake_client

        response = self.client.get(
            reverse('dashboard-v1:search'),
            {'q': 'osa', 'record_type': 'isad'}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        fake_index.search.assert_called_once_with(
            'osa',
            {
                'limit': 20,
                'offset': 0,
                'filter': (
                    'record_type IN ["isad"] AND '
                    f'(archival_unit_id IN [{allowed_series.id}] OR '
                    f'series_id IN [{allowed_series.id}] OR '
                    f'(record_type = "isad" AND ams_id IN [{allowed_series.id}]) OR '
                    f'(record_type = "archival_unit" AND ams_id IN [{allowed_series.id}]))'
                )
            }
        )

    @patch('dashboard.views.search_views.meilisearch.Client')
    def test_search_returns_503_when_meilisearch_fails(self, client_class):
        fake_client = Mock()
        fake_client.index.side_effect = RuntimeError('meili down')
        client_class.return_value = fake_client

        response = self.client.get(reverse('dashboard-v1:search'), {'q': 'osa'})

        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertEqual(response.data['detail'], 'Search service unavailable.')
