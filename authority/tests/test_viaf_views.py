from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase


class VIAFTest(APITestCase):
    """ Testing VIAF endpoint """

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_get_empty_result(self):
        response = self.client.get(reverse('authority-v1:viaf-list'), {'query': ''})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_person(self):
        response = self.client.get(reverse('authority-v1:viaf-list'), {'query': 'Lenin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['viaf_id'] == "http://www.viaf.org/viaf/7393146", records))) == 1
        self.assertTrue(has_result)

    def test_get_corporation(self):
        response = self.client.get(reverse('authority-v1:viaf-list'), {'query': 'Reuters', 'type': 'corporation'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['viaf_id'] == "http://www.viaf.org/viaf/132548028", records))) == 1
        self.assertTrue(has_result)

    def test_get_country(self):
        response = self.client.get(reverse('authority-v1:viaf-list'), {'query': 'Russia', 'type': 'country'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['viaf_id'] == "http://www.viaf.org/viaf/124251745", records))) == 1
        self.assertTrue(has_result)

    def test_get_place(self):
        response = self.client.get(reverse('authority-v1:viaf-list'), {'query': 'Budapest', 'type': 'place'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        records = response.data
        has_result = len(list(filter(lambda r: r['viaf_id'] == "http://www.viaf.org/viaf/154759119", records))) == 1
        self.assertTrue(has_result)
