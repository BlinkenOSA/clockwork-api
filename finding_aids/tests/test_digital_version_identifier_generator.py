from django.test import TestCase

from archival_unit.models import ArchivalUnit
from archival_unit.signals import update_isad_when_archival_unit_saved
from container.models import Container
from container.signals import update_finding_aids_index_upon_container_save
from digitization.models import DigitalVersion
from django.db.models.signals import post_save, pre_delete
from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator
from finding_aids.models import FindingAidsEntity
from finding_aids.signals import update_finding_aids_index, remove_finding_aids_index


class DigitalVersionIdentifierGeneratorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        post_save.disconnect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.disconnect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.disconnect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.disconnect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.connect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.connect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.connect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)

    def setUp(self):
        super().setUp()


    def _entity(self, pk=174492):
        return FindingAidsEntity.objects.select_related("container", "archival_unit").get(pk=pk)

    def test_detect_true_when_entity_has_digital_versions(self):
        entity = self._entity()
        self.assertEqual(entity.archival_reference_code, "HU OSA 206-3-1/3:2")

        DigitalVersion.objects.create(
            finding_aids_entity=entity,
            identifier="HU_OSA_206_3_1_0003_0002",
            filename="image.jpg",
        )

        generator = DigitalVersionIdentifierGenerator(entity)
        self.assertTrue(generator.detect())

    def test_detect_true_when_container_has_digital_version_flag(self):
        entity = self._entity(174491)
        entity.container.digital_version_exists = True

        generator = DigitalVersionIdentifierGenerator(entity)
        self.assertTrue(generator.detect())

    def test_detect_false_when_no_digital_data_exists(self):
        entity = self._entity(174491)

        generator = DigitalVersionIdentifierGenerator(entity)
        self.assertFalse(generator.detect())

    def test_detect_available_online_paths(self):
        entity = self._entity(174491)

        entity.digital_version_online = True
        self.assertTrue(DigitalVersionIdentifierGenerator(entity).detect_available_online())

        entity.digital_version_online = False
        entity.container.digital_version_online = True
        self.assertTrue(DigitalVersionIdentifierGenerator(entity).detect_available_online())

        entity.container.digital_version_online = False
        self.assertFalse(DigitalVersionIdentifierGenerator(entity).detect_available_online())

    def test_generate_identifier_entity_level_l1_from_fixture_reference_code(self):
        entity = self._entity(174492)
        entity.digital_version_exists = True

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(
            generator.generate_identifier(),
            "HU_OSA_206_3_1_0003_0002",
        )

    def test_generate_identifier_entity_level_l2(self):
        entity = self._entity(174492)
        entity.digital_version_exists = True
        entity.description_level = "L2"
        entity.sequence_no = 9

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(
            generator.generate_identifier(),
            "HU_OSA_206_3_1_0003_0002_0009",
        )

    def test_generate_identifier_container_barcode_fallback(self):
        entity = self._entity(174489)
        entity.container.digital_version_exists = True
        entity.container.barcode = "BC-206-3-1"

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "BC-206-3-1")

    def test_generate_identifier_container_legacy_id_fallback(self):
        entity = self._entity(174489)
        entity.container.digital_version_exists = True
        entity.container.barcode = ""
        entity.container.legacy_id = "206/2000-3:5"

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "206/2000-3:5")

    def test_generate_identifier_container_generated_fallback(self):
        entity = self._entity(174489)
        entity.container.digital_version_exists = True
        entity.container.barcode = ""
        entity.container.legacy_id = ""

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "HU_OSA_206_3_1_0001")

    def test_generate_identifier_empty_when_no_digital_data(self):
        entity = self._entity(174491)

        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "")
