from django.test import TestCase

from accession.models import AccessionMethod
from accession.serializers import AccessionWriteSerializer


class FieldTest(TestCase):
    """ Test module for Fields """
    fixtures = ['donor']

    def setUp(self):
        self.accession_method = AccessionMethod.objects.create(
            method='Test method'
        )

    def test_approximate_date_serializer_field_year(self):
        accession = {
            'title': 'Accession Test',
            'method': self.accession_method.id,
            'donor': 15,
            'transfer_date': '1999',
            'creation_date_from': '1995',
            'creation_date_to': '2000',
            'items': []
        }
        serializer = AccessionWriteSerializer(data=accession)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['transfer_date'], '1999')


    def test_approximate_date_serializer_field_year_mohth(self):
        accession = {
            'title': 'Accession Test',
            'method': self.accession_method.id,
            'donor': 15,
            'transfer_date': '1999-12',
            'creation_date_from': '1995',
            'creation_date_to': '2000',
            'items': []
        }
        serializer = AccessionWriteSerializer(data=accession)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['transfer_date'], '1999-12')


    def test_approximate_date_serializer_field_year_mohth_day(self):
        accession = {
            'title': 'Accession Test',
            'method': self.accession_method.id,
            'donor': 15,
            'transfer_date': '1999-12-31',
            'creation_date_from': '1995',
            'creation_date_to': '2000',
            'items': []
        }
        serializer = AccessionWriteSerializer(data=accession)
        serializer.is_valid()
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.data['transfer_date'], '1999-12-31')

    def test_approximate_date_serializer_field_invalid_date(self):
        accession = {
            'title': 'Accession Test',
            'method': self.accession_method.id,
            'donor': 15,
            'transfer_date': '1999-12-32',
            'creation_date_from': '1995',
            'creation_date_to': '2000',
            'items': []
        }
        serializer = AccessionWriteSerializer(data=accession)
        serializer.is_valid()
        self.assertTrue('transfer_date' in serializer.errors)
