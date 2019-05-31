from django.contrib.auth.models import User

from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from authority.models import Country


class CountryViewAPITest(APITestCase):
    def setUp(self):
        Country.objects.create(alpha2='AF', alpha3='AFG', country='Afghanistan')
        Country.objects.create(alpha2='AL', alpha3='ALB', country='Albania')
        self.user = User.objects.create_superuser(username='testuser',
                                                  email='testuser@eqar.eu',
                                                  password='testpassword')
        self.user.save()
        self.token = Token.objects.get(user__username='testuser')
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + self.token.key)
