from rest_framework import status
from rest_framework.reverse import reverse
from unittest.mock import patch

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class WikipediaTest(TestViewsBaseClass):
    """ Testing Wikipedia endpoint """

    def setUp(self):
        super().setUp()

    @patch('authority.views.wikipedia_views.wikipedia.search', return_value=['Vladimir Lenin', 'Lenin'])
    @patch('authority.views.wikipedia_views.wikipedia.set_lang')
    def test_get_query(self, mock_set_lang, mock_search):
        response = self.client.get(reverse('authority-v1:wikipedia-list'), {'query': 'Lenin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 24)
        self.assertIn(
            {'name': 'Vladimir Lenin', 'url': 'http://en.wikipedia.org/wiki/Vladimir Lenin'},
            response.data
        )
        self.assertIn(
            {'name': 'Vladimir Lenin', 'url': 'http://hu.wikipedia.org/wiki/Vladimir Lenin'},
            response.data
        )
        self.assertEqual(mock_set_lang.call_count, 12)
        self.assertEqual(mock_search.call_count, 12)
