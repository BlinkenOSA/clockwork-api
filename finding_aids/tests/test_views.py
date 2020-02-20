from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class FindingAidsPublishTest(APITestCase):
    """ Testing Finding Aids publishing endpoints"""
    fixtures = ['finding_aids', 'carrier_types', 'primary_types']

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.container_id = 5675
        self.series_id = 908
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_fa_create(self):
        finding_aids = {
            'folder_no': 3,
            'title': 'Test Folder'
        }
        response = self.client.post(
            reverse('finding_aids-v1:finding_aids-create', kwargs={'container_id': self.container_id}),
            data=finding_aids
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], finding_aids['title'])
        self.assertEqual(response.data['container'], self.container_id)
        self.assertEqual(response.data['archival_unit'], self.series_id)

    def test_publish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': '174492'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': '174492'}))
        self.assertEqual(response.data['published'], True)
        self.assertEqual(response.data['user_published'], self.user.username)

    def test_unpublish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'unpublish', 'pk': '174491'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': '174491'}))
        self.assertEqual(response.data['published'], False)
        self.assertEqual(response.data['user_published'], "")

    def test_publish_non_existent(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_select_by_container(self):
        response = self.client.get(reverse('finding_aids-v1:finding_aids-select', kwargs={'container_id': '5675'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
