from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from finding_aids.models import FindingAidsEntity


class FindingAidsPublishTest(APITestCase):
    """ Testing Finding Aids publishing endpoints"""
    fixtures = ['carrier_types', 'primary_types']

    def setUp(self):
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
        self.series = ArchivalUnit.objects.create(
            fonds=206,
            subfonds=3,
            series=1,
            level='S',
            title='Audiovisual Recordings of Public Events',
            parent=self.subfonds
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.get(pk=1),
            container_no=1
        )
        self.finding_aids = FindingAidsEntity.objects.create(
            container=self.container,
            archival_unit=self.container.archival_unit,
            folder_no=2,
            title='Test Folder'
        )
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_fa_create(self):
        finding_aids = {
            'folder_no': 1,
            'title': 'Test Folder'
        }
        response = self.client.post(
            reverse('finding_aids-v1:finding_aids-create', kwargs={'container_id': self.container.id}),
            data=finding_aids
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], finding_aids['title'])
        self.assertEqual(response.data['container'], self.container.id)
        self.assertEqual(response.data['archival_unit'], self.series.id)

    def test_publish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': self.finding_aids.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': self.finding_aids.id}))
        self.assertEqual(response.data['published'], True)
        self.assertEqual(response.data['user_published'], self.user.username)

    def test_unpublish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'unpublish', 'pk': self.finding_aids.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': self.finding_aids.id}))
        self.assertEqual(response.data['published'], False)
        self.assertEqual(response.data['user_published'], "")

    def test_publish_non_existent(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)