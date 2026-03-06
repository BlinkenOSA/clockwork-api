from django.test import TestCase

from isaar.models import (
    Isaar,
    IsaarParallelName,
    IsaarOtherName,
    IsaarStandardizedName,
    IsaarCorporateBodyIdentifier,
    IsaarPlace,
    IsaarPlaceQualifier,
)
from isaar.serializers import IsaarReadSerializer


class IsaarReadSerializerTests(TestCase):
    def test_nested_related_fields_present(self):
        isaar = Isaar.objects.create(
            name='Nested Entity',
            type='C',
            date_existence_from='1990-01-01',
            date_existence_to='2000-01-01',
        )
        qualifier = IsaarPlaceQualifier.objects.create(id=2, qualifier='Seat')

        IsaarParallelName.objects.create(isaar=isaar, name='Entidad')
        IsaarOtherName.objects.create(isaar=isaar, name='Old Entity')
        IsaarStandardizedName.objects.create(isaar=isaar, name='NESTED ENTITY')
        IsaarCorporateBodyIdentifier.objects.create(isaar=isaar, identifier='ID-123')
        IsaarPlace.objects.create(isaar=isaar, place='Budapest', place_qualifier=qualifier)

        data = IsaarReadSerializer(isaar).data

        self.assertEqual(len(data['parallel_names']), 1)
        self.assertEqual(len(data['other_names']), 1)
        self.assertEqual(len(data['standardized_names']), 1)
        self.assertEqual(len(data['corporate_body_identifiers']), 1)
        self.assertEqual(len(data['places']), 1)
        self.assertEqual(data['places'][0]['place_qualifier']['qualifier'], 'Seat')
