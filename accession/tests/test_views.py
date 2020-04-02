from rest_framework.reverse import reverse
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token


class AccessionViewTest(APITestCase):
    """ Testing Accession endpoints """
    fixtures = ['accession']

    def setUp(self):
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)

    def test_filter_class(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'search': 'research institute'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_year(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'transfer_year': '1995'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_year_not_exists(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'transfer_year': '1996'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_fonds(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': '300'})
        self.assertEqual(response.data['count'], 1)

    def test_fonds_not_exists(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': '301'})
        self.assertEqual(response.data['count'], 0)

    def test_fonds_not_a_number(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': 'abc'})
        self.assertEqual(response.data['count'], 0)