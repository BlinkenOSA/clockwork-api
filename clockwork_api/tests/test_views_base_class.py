from rest_framework.test import APITestCase, APIClient
from django.contrib.auth.models import User

from accounts.models import UserProfile


class TestViewsBaseClass(APITestCase):
    def setUp(self):
        self.user = User.objects.create_superuser(
            username='testuser',
            email='testuser@archivum.org',
            password='testpassword'
        )
        self.user_profile = UserProfile.objects.create(user=self.user)
        self.client.force_authenticate(user=self.user)
