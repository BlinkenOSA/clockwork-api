from django.test import TestCase, override_settings

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from workflow.serializers.archival_unit_serializer import ArchivalUnitSerializer
from workflow.serializers.container_serializers import ContainerDigitizedSerializer
from workflow.views.digital_object_views import (
    matches_any_pattern,
    make_ordinal,
    get_mime_category,
    get_doi,
    get_label,
    get_access_copy_actions,
)


class WorkflowHelpersTests(TestCase):
    def test_matches_any_pattern(self):
        self.assertTrue(matches_any_pattern('HU_OSA_386_1_1_0001.pdf'))
        self.assertTrue(matches_any_pattern('HU_OSA_386_1_1_0001_0001.jpg'))
        self.assertFalse(matches_any_pattern('invalid_name.txt'))

    def test_make_ordinal(self):
        self.assertEqual(make_ordinal(1), '1st')
        self.assertEqual(make_ordinal(2), '2nd')
        self.assertEqual(make_ordinal(11), '11th')

    def test_get_mime_category(self):
        self.assertEqual(get_mime_category('mp4'), 'Moving Image')
        self.assertEqual(get_mime_category('mp3'), 'Audio')
        self.assertEqual(get_mime_category('jpg'), 'Still Image')

    def test_get_doi_and_label(self):
        self.assertEqual(get_doi('HU_OSA_386_1_1_0001_0001_P001'), 'HU_OSA_386_1_1_0001_0001')
        self.assertEqual(get_label('HU_OSA_386_1_1_0001_0001_P001'), 'Page 1')

    @override_settings(
        DIGITAL_OBJECTS_STORAGE_TEXT_SERVER='text.example',
        DIGITAL_OBJECTS_STORAGE_TEXT_BASE_DIR='/text/',
        DIGITAL_OBJECTS_STORAGE_AUDIO_SERVER='audio.example',
        DIGITAL_OBJECTS_STORAGE_AUDIO_BASE_DIR='/audio/',
    )
    def test_get_access_copy_actions(self):
        textual = get_access_copy_actions('HU_OSA_386_1_1_0001_0001', 'Textual')
        self.assertEqual(textual['target_server'], 'text.example')
        self.assertTrue(textual['filename'].endswith('.pdf'))

        audio = get_access_copy_actions('HU_OSA_386_1_1_0001_0001', 'Audio')
        self.assertEqual(audio['target_server'], 'audio.example')
        self.assertTrue(audio['filename'].endswith('.mp3'))


class WorkflowSerializersTests(TestCase):
    fixtures = ['carrier_types']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=1300, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1300,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1300,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_WORK',
        )

    def test_archival_unit_workflow_serializer(self):
        data = ArchivalUnitSerializer(self.series).data
        self.assertEqual(data['fonds']['number'], 1300)
        self.assertEqual(data['subfonds']['number'], 1)
        self.assertEqual(data['series']['number'], 1)

    def test_container_digitized_serializer(self):
        data = ContainerDigitizedSerializer(self.container).data
        self.assertEqual(data['barcode'], 'HU_OSA_WORK')
        self.assertEqual(data['carrier_type'], self.container.carrier_type.type)
        self.assertEqual(data['archival_unit']['series']['number'], 1)
