from django.test import TestCase

from authority.models import Country
from donor.serializers import DonorSerializer


class DonorSerializerTest(TestCase):
    """ Test module for Donor Serializer """
    fixtures = ['country']

    def setUp(self):
        self.donor = {
            'postal_code': '1051',
            'country': Country.objects.get(country='Hungary').id,
            'city': 'Budapest',
            'address': 'Arany Janos u. 32.',
            'email': 'info@osaarchivum.org'
        }

    def test_donor_invalid(self):
        serializer = DonorSerializer(data=self.donor)
        serializer.is_valid()
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['non_field_errors'][0], "Name or Corporation Name is mandatory!")

    def test_donor_valid(self):
        self.donor['first_name'] = 'John'
        self.donor['last_name'] = 'Doe'
        serializer = DonorSerializer(data=self.donor)
        self.assertTrue(serializer.is_valid())
