from django.test import TestCase

from accession.models import AccessionMethod
from accession.serializers import AccessionWriteSerializer
from donor.models import Donor


class AccessionWriteSerializerTests(TestCase):
    fixtures = ['accession']

    def _base_payload(self):
        method = AccessionMethod.objects.first()
        donor = Donor.objects.first()
        return {
            'title': 'Test accession',
            'transfer_date': '2020-01-01',
            'method': method.id,
            'donor': donor.id,
            'items': [
                {'quantity': 1, 'container': 'box', 'content': ''}
            ],
        }

    def test_validate_creation_date_range_rejects_inverted(self):
        data = self._base_payload()
        data.update({
            'creation_date_from': '2021-01-01',
            'creation_date_to': '2020-01-01',
        })

        serializer = AccessionWriteSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('non_field_errors', serializer.errors)
        self.assertIn('Date from value is bigger than date to value.', serializer.errors['non_field_errors'])

    def test_validate_creation_date_range_accepts_valid(self):
        data = self._base_payload()
        data.update({
            'creation_date_from': '2020-01-01',
            'creation_date_to': '2021-01-01',
        })

        serializer = AccessionWriteSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
