import json
from unittest.mock import Mock, patch

from rest_framework import status
from rest_framework.reverse import reverse
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class LCSHTest(TestViewsBaseClass):
    """Test the LCSH endpoint without depending on the live LoC service."""

    def setUp(self):
        super().setUp()
        session_patch = patch('authority.views.lcsh_views.Session')
        self.session = session_patch.start().return_value
        self.addCleanup(session_patch.stop)

    def mock_lcsh_response(self, lcsh_id, name):
        payload = [
            'atom:feed',
            {'xmlns:atom': 'http://www.w3.org/2005/Atom'},
            ['atom:entry', {},
             ['atom:title', {}, name],
             ['atom:link', {'rel': 'alternate', 'href': lcsh_id}]],
        ]
        self.session.get.return_value = Mock(status_code=200, text=json.dumps(payload))

    def test_get_empty_result(self):
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': ''})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
        self.session.get.assert_not_called()

    def test_get_genre(self):
        self.mock_lcsh_response('http://id.loc.gov/authorities/genreForms/gf2011026321', 'Horror films')
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': 'Horror', 'type': 'genre'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{
            'lcsh_id': 'http://id.loc.gov/authorities/genreForms/gf2011026321',
            'name': 'Horror films',
        }])
        self.session.get.assert_called_once_with(
            'https://id.loc.gov/search/',
            params={'q': ['Horror', 'cs:http://id.loc.gov/authorities/genreForms'], 'format': 'json'},
        )

    def test_get_subject(self):
        self.mock_lcsh_response('http://id.loc.gov/authorities/subjects/sh85026379', 'Human rights')
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': 'Human Rights', 'type': 'subject'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [{
            'lcsh_id': 'http://id.loc.gov/authorities/subjects/sh85026379',
            'name': 'Human rights',
        }])
        self.session.get.assert_called_once_with(
            'https://id.loc.gov/search/',
            params={'q': ['Human Rights', 'cs:http://id.loc.gov/authorities/subjects'], 'format': 'json'},
        )
