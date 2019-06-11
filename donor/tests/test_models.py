from django.test import TestCase

from authority.models import Country
from donor.models import Donor


class DonorTest(TestCase):
    """ Test module for Donor model """
    fixtures = ['country']

    def setUp(self):
        self.donor = Donor.objects.create(
            name='John, Doe',
            first_name='John',
            last_name='Doe',
            postal_code='1051',
            country=Country.objects.get(country='Hungary'),
            city='Budapest',
            address='Arany Janos u. 32.',
            email='info@osaarchivum.org'
        )

    def test_get_address(self):
        self.assertEqual(self.donor.get_address(), '1051 Hungary, Budapest, Arany Janos u. 32.')