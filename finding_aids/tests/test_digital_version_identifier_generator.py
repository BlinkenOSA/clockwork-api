from types import SimpleNamespace

from django.test import SimpleTestCase

from finding_aids.generators.digital_version_identifier_generator import DigitalVersionIdentifierGenerator


class _CountStub:
    def __init__(self, value):
        self.value = value

    def count(self):
        return self.value


class DigitalVersionIdentifierGeneratorTests(SimpleTestCase):
    def _entity(
        self,
        *,
        dv_count=0,
        entity_dv_exists=False,
        container_dv_exists=False,
        available_online=False,
        entity_dv_online=False,
        container_dv_online=False,
        description_level="L1",
        reference_code="HU OSA 300-1",
        container_no=12,
        folder_no=34,
        sequence_no=5,
        barcode="",
        legacy_id="",
    ):
        container = SimpleNamespace(
            digital_version_exists=container_dv_exists,
            digital_version_online=container_dv_online,
            container_no=container_no,
            barcode=barcode,
            legacy_id=legacy_id,
        )
        return SimpleNamespace(
            digital_versions=_CountStub(dv_count),
            digital_version_exists=entity_dv_exists,
            available_online=available_online,
            digital_version_online=entity_dv_online,
            description_level=description_level,
            archival_unit=SimpleNamespace(reference_code=reference_code),
            container=container,
            folder_no=folder_no,
            sequence_no=sequence_no,
        )

    def test_detect_true_for_entity_digital_versions(self):
        entity = self._entity(dv_count=1)
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertTrue(generator.detect())

    def test_detect_true_for_container_fallback(self):
        entity = self._entity(container_dv_exists=True)
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertTrue(generator.detect())

    def test_detect_false_when_no_flags_or_versions(self):
        entity = self._entity()
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertFalse(generator.detect())

    def test_detect_available_online_entity_and_container_paths(self):
        self.assertTrue(DigitalVersionIdentifierGenerator(self._entity(available_online=True)).detect_available_online())
        self.assertTrue(DigitalVersionIdentifierGenerator(self._entity(container_dv_online=True)).detect_available_online())
        self.assertFalse(DigitalVersionIdentifierGenerator(self._entity()).detect_available_online())

    def test_generate_identifier_entity_level_l1(self):
        entity = self._entity(dv_count=2, description_level="L1")
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "HU_OSA_300_1_0012_0034")

    def test_generate_identifier_entity_level_l2(self):
        entity = self._entity(dv_count=2, description_level="L2")
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "HU_OSA_300_1_0012_0034_0005")

    def test_generate_identifier_container_fallback_barcode(self):
        entity = self._entity(container_dv_exists=True, barcode="BC-123")
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "BC-123")

    def test_generate_identifier_container_fallback_legacy_id(self):
        entity = self._entity(container_dv_exists=True, legacy_id="LEG-7")
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "LEG-7")

    def test_generate_identifier_container_fallback_generated(self):
        entity = self._entity(container_dv_exists=True)
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "HU_OSA_300_1_0012")

    def test_generate_identifier_empty_when_no_digital_data(self):
        entity = self._entity()
        generator = DigitalVersionIdentifierGenerator(entity)

        self.assertEqual(generator.generate_identifier(), "")
