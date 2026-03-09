from django.test import TestCase

from accession.serializers import AccessionWriteSerializer
from accession.tests.helpers import make_accession_method
from donor.tests.helpers import make_donor


class AccessionWriteSerializerTests(TestCase):
    def _base_payload(self):
        method = make_accession_method()
        donor = make_donor()
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
