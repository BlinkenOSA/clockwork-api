from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class LCSHTest(APITestCase):
    """ Testing LCSH endpoint """

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_get_empty_result(self):
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': ''})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_genre(self):
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': 'Horror', 'type': 'genre'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['lcsh_id'] == "http://id.loc.gov/authorities/genreForms/gf2011026321",
                                     records))) == 1
        self.assertTrue(has_result)

    def test_get_subject(self):
        response = self.client.get(reverse('authority-v1:lcsh-list'), {'query': 'Human Rights', 'type': 'subject'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['lcsh_id'] == "http://id.loc.gov/authorities/subjects/sh85026379",
                                     records))) == 1
        self.assertTrue(has_result)
