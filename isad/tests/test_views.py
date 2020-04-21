from rest_framework import status
from rest_framework.reverse import reverse
from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from isad.models import Isad


class IsadPublishTest(TestViewsBaseClass):
    """ Testing ISAD publishing endpoints"""

    def setUp(self):
        self.init()
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
            year_from=1991
        )

    def test_publish(self):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'publish', 'pk': self.isad.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('isad-v1:isad-detail', kwargs={'pk': self.isad.id}))
        self.assertEqual(response.data['published'], True)
        self.assertEqual(response.data['user_published'], self.user.username)

    def test_unpublish(self):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'unpublish', 'pk': self.isad.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('isad-v1:isad-detail', kwargs={'pk': self.isad.id}))
        self.assertEqual(response.data['published'], False)
        self.assertEqual(response.data['user_published'], "")

    def test_publish_non_existent(self):
        response = self.client.put(reverse('isad-v1:isad-publish', kwargs={'action': 'publish', 'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
