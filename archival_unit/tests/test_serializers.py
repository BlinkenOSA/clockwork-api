from django.test import TestCase
from archival_unit.serializers import ArchivalUnitWriteSerializer


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
