from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class DonorViewTest(APITestCase):
    """ Testing Donor endpoints """
    fixtures = ['donor']

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_filter_class(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support scheme'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_class_not_exists(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support schema'})
        self.assertEqual(response.data['count'], 0)