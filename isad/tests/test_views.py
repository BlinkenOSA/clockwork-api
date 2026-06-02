from rest_framework import status
from rest_framework.reverse import reverse
from unittest.mock import patch
from archival_unit.models import ArchivalUnit
from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from isad.models import Isad


class IsadPublishTest(NoIndexSignalsMixin, TestViewsBaseClass):
    """ Testing ISAD publishing endpoints"""

    def setUp(self):
        super().setUp()
        self.fonds = ArchivalUnit.objects.create(
            fonds=206,
            level='F',
            title='Records of the Open Society Archives at Central European University'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            level='SF',
            title='Public Events',
            parent=self.fonds
        )
        self.isad = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1991
        )

    @patch("isad.models.ensure_ark")
    def test_publish(self, mock_ensure_ark):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'publish', 'pk': self.isad.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('isad-v1:isad-detail', kwargs={'pk': self.isad.id}))
        self.assertEqual(response.data['published'], True)
        self.assertEqual(response.data['user_published'], self.user.username)
        mock_ensure_ark.assert_called_once()

    def test_unpublish(self):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'unpublish', 'pk': self.isad.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('isad-v1:isad-detail', kwargs={'pk': self.isad.id}))
        self.assertEqual(response.data['published'], False)
        self.assertEqual(response.data['user_published'], "")

    def test_publish_non_existent(self):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'publish', 'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
