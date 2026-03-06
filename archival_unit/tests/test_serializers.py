from django.test import TestCase

from archival_unit.models import ArchivalUnit
from archival_unit.serializers import (
    ArchivalUnitWriteSerializer,
    ArchivalUnitPreCreateSerializer,
    ArchivalUnitReadSerializer,
    ArchivalUnitSelectSerializer,
)


class ArchivalUnitSerializerTest(TestCase):
    """ Test module for ArchivalUnit Serializer """
    def test_archival_unit_wrong_status(self):
        archival_unit = {
            'fonds': 206,
            'level': 'F',
            'title': 'Records of the Open Society Archives at Central European University',
            'status': 'Start'
        }
        serializer = ArchivalUnitWriteSerializer(data=archival_unit)
        serializer.is_valid()
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['status'][0], "Status should be either: 'Final' or 'Draft'")

    def test_archival_unit_wrong_level(self):
        archival_unit = {
            'fonds': 206,
            'level': 'FN',
            'title': 'Records of the Open Society Archives at Central European University',
            'status': 'Draft'
        }
        serializer = ArchivalUnitWriteSerializer(data=archival_unit)
        serializer.is_valid()
        self.assertFalse(serializer.is_valid())
        self.assertEqual(serializer.errors['level'][0], "Level should be either: 'Fonds', 'Subfonds', 'Series'")

    def test_precreate_serializer_for_fonds(self):
        fonds = ArchivalUnit.objects.create(
            fonds=100,
            level='F',
            title='Fonds Title',
            acronym='FT'
        )
        data = ArchivalUnitPreCreateSerializer(fonds).data
        self.assertEqual(data['parent'], fonds.id)
        self.assertEqual(data['fonds_title'], 'Fonds Title')
        self.assertEqual(data['fonds_acronym'], 'FT')
        self.assertIsNone(data['subfonds_title'])
        self.assertIsNone(data['subfonds_acronym'])
        self.assertEqual(data['level'], 'SF')

    def test_precreate_serializer_for_subfonds(self):
        fonds = ArchivalUnit.objects.create(
            fonds=100,
            level='F',
            title='Fonds Title',
            acronym='FT'
        )
        subfonds = ArchivalUnit.objects.create(
            fonds=100,
            subfonds=1,
            level='SF',
            title='Subfonds Title',
            acronym='SFT',
            parent=fonds
        )
        data = ArchivalUnitPreCreateSerializer(subfonds).data
        self.assertEqual(data['fonds_title'], 'Fonds Title')
        self.assertEqual(data['fonds_acronym'], 'FT')
        self.assertEqual(data['subfonds_title'], 'Subfonds Title')
        self.assertEqual(data['subfonds_acronym'], 'SFT')
        self.assertEqual(data['level'], 'S')

    def test_read_serializer_titles_for_series(self):
        fonds = ArchivalUnit.objects.create(
            fonds=100,
            level='F',
            title='Fonds Title',
            acronym='FT'
        )
        subfonds = ArchivalUnit.objects.create(
            fonds=100,
            subfonds=1,
            level='SF',
            title='Subfonds Title',
            acronym='SFT',
            parent=fonds
        )
        series = ArchivalUnit.objects.create(
            fonds=100,
            subfonds=1,
            series=1,
            level='S',
            title='Series Title',
            parent=subfonds
        )
        data = ArchivalUnitReadSerializer(series).data
        self.assertEqual(data['fonds_title'], 'Fonds Title')
        self.assertEqual(data['fonds_acronym'], 'FT')
        self.assertEqual(data['subfonds_title'], 'Subfonds Title')
        self.assertEqual(data['subfonds_acronym'], 'SFT')

    def test_select_serializer_counts(self):
        fonds = ArchivalUnit.objects.create(
            fonds=200,
            level='F',
            title='Fonds Title'
        )
        subfonds = ArchivalUnit.objects.create(
            fonds=200,
            subfonds=1,
            level='SF',
            title='Subfonds Title',
            parent=fonds
        )
        series = ArchivalUnit.objects.create(
            fonds=200,
            subfonds=1,
            series=1,
            level='S',
            title='Series Title',
            parent=subfonds
        )

        fonds_data = ArchivalUnitSelectSerializer(fonds).data
        series_data = ArchivalUnitSelectSerializer(series).data

        self.assertIsNone(fonds_data['container_count'])
        self.assertIsNone(fonds_data['folder_count'])
        self.assertEqual(series_data['container_count'], 0)
        self.assertEqual(series_data['folder_count'], 0)
