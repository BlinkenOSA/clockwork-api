from unittest import skip

from django.db.models.signals import post_save, pre_delete
from django.test import TestCase, override_settings
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from archival_unit.signals import update_isad_when_archival_unit_saved
from container.models import Container
from container.signals import update_finding_aids_index_upon_container_save
from controlled_list.models import PrimaryType
from digitization.models import DigitalVersion
from finding_aids.models import FindingAidsEntity
from finding_aids.signals import remove_finding_aids_index, update_finding_aids_index
from isad.models import Isad
from isad.signals import remove_isad_index, update_isad_index
from unittest.mock import Mock, patch


class _FixtureSignalsSafeTestCase(TestCase):
    fixtures = [
        "access_rights",
        "archival_unit_themes",
        "authority_genres_for_finding_aids",
        "finding_aids",
    ]

    @classmethod
    def setUpClass(cls):
        post_save.disconnect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.disconnect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.disconnect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.disconnect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        post_save.disconnect(update_isad_index, sender=Isad)
        pre_delete.disconnect(remove_isad_index, sender=Isad)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.connect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.connect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.connect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        post_save.connect(update_isad_index, sender=Isad)
        pre_delete.connect(remove_isad_index, sender=Isad)


@override_settings(BASE_URL="https://catalog.example", BASE_IMAGE_URI="https://images.example/iiif/2/")
class CatalogIiifFixtureBackedTests(_FixtureSignalsSafeTestCase):
    @skip
    def _mark_entity_as_still_image_online(self, entity_id=174491):
        still_type, _ = PrimaryType.objects.get_or_create(type="Still Image")
        entity = FindingAidsEntity.objects.get(pk=entity_id)
        entity.primary_type = still_type
        entity.digital_version_online = True
        entity.save(update_fields=["primary_type", "digital_version_online"])
        return entity

    @skip
    def test_archival_units_manifest_view_with_real_fixture_entity(self):
        entity = self._mark_entity_as_still_image_online()

        factory = Mock()
        manifest = Mock()
        seq = Mock()
        canvas = Mock()
        factory.manifest.return_value = manifest
        manifest.sequence.return_value = seq
        seq.canvas.return_value = canvas
        manifest.toJSON.return_value = {"manifest": "ok"}

        with patch("catalog.views.iiif_views.archival_units_image_manifest_view.ManifestFactory", return_value=factory):
            response = self.client.get(reverse("catalog-v1:archival-units-manifest-view", args=[908]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"manifest": "ok"})
        seq.canvas.assert_called()
        self.assertIn(entity.archival_reference_code, seq.canvas.call_args.kwargs["ident"])

    @skip
    def test_finding_aids_image_manifest_v2_with_real_fixture_entity(self):
        entity = self._mark_entity_as_still_image_online()
        DigitalVersion.objects.create(
            finding_aids_entity=entity,
            identifier="HU_OSA_206_3_1_0003_0001",
            filename="test image.jpg",
            available_online=True,
        )

        factory = Mock()
        manifest = Mock()
        seq = Mock()
        canvas = Mock()
        factory.manifest.return_value = manifest
        manifest.sequence.return_value = seq
        seq.canvas.return_value = canvas
        manifest.toJSON.return_value = {"manifest": "v2"}

        with patch("catalog.views.iiif_views.finding_aids_image_manifest_view.ManifestFactory", return_value=factory):
            response = self.client.get(reverse("catalog-v1:finding-aids-manifest-mobile-view", args=[entity.catalog_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"manifest": "v2"})
        seq.canvas.assert_called_once_with(ident="Image", label="Image")

    @skip
    def test_finding_aids_iiif_v3_with_real_fixture_entity(self):
        entity = self._mark_entity_as_still_image_online()
        dv = DigitalVersion.objects.create(
            finding_aids_entity=entity,
            identifier="AA_BB_CC_DD_EE_FF",
            filename="v3-image.jpg",
            label="Page 1",
            available_online=True,
        )

        manifest = Mock()
        canvas = Mock()
        manifest.make_canvas_from_iiif.return_value = canvas
        manifest.json.return_value = '{"ok": true}'

        with patch("catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view.Manifest", return_value=manifest):
            response = self.client.get(reverse("catalog-v1:finding-aids-manifest-view", args=[entity.catalog_id]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True})
        self.assertTrue(manifest.make_canvas_from_iiif.called)
        called_url = manifest.make_canvas_from_iiif.call_args.kwargs["url"]
        self.assertIn("catalog%2FAA_BB_CC_DD_EE%2F", called_url)
        self.assertIn(dv.filename, called_url)
