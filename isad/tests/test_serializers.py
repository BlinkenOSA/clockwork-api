from django.test import TestCase

from archival_unit.models import ArchivalUnit
from authority.models import Language
from isad.models import Isad, IsadCreator
from isad.serializers.isad_serializers import IsadReadSerializer, IsadPreCreateSerializer


class IsadSerializerTests(TestCase):
    def setUp(self):
        self.fonds = ArchivalUnit.objects.create(fonds=1000, level='F', title='Fonds')
        self.language = Language.objects.create(language='English')

    def test_precreate_serializer_maps_archival_unit_fields(self):
        data = IsadPreCreateSerializer(self.fonds).data
        self.assertEqual(data['archival_unit'], self.fonds.id)
        self.assertEqual(data['reference_code'], self.fonds.reference_code)
        self.assertEqual(data['title'], self.fonds.title)
        self.assertEqual(data['description_level'], 'F')

    def test_read_serializer_exposes_title_full_and_nested_creators(self):
        isad = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1990,
        )
        isad.language.add(self.language)
        IsadCreator.objects.create(isad=isad, creator='Creator Name')

        data = IsadReadSerializer(isad).data
        self.assertEqual(data['title_full'], self.fonds.title_full)
        self.assertEqual(len(data['creators']), 1)
        self.assertEqual(data['creators'][0]['creator'], 'Creator Name')
