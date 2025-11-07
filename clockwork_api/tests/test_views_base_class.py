from rest_framework import status
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User

from accounts.models import UserProfile


class TestViewsBaseClass(APITestCase):
    def init(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()

        self.user_profile = UserProfile.objects.create(user=self.user)

        self.client.force_authenticate(self.user)

        # url = reverse('jwt-create')
        # resp = self.client.post(url, {'username': 'testuser', 'password': 'testpassword'}, format='json')
        # self.assertEqual(resp.status_code, status.HTTP_200_OK)
        # self.assertTrue('token' in resp.data)
        # token = resp.data['token']
        # self.client.credentials(HTTP_AUTHORIZATION='JWT ' + token)