from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from catalog.views.iiif_views.finding_aids_image_manifest_view import FindingAidsImageManifestView


class FindingAidsImageManifestViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FindingAidsImageManifestView()

    @override_settings(BASE_URL="https://catalog.example", BASE_IMAGE_URI="https://images.example/iiif/2/")
    def test_get_builds_v2_manifest_for_still_image_online_record(self):
        fa_entity = SimpleNamespace(
            primary_type=SimpleNamespace(type="Still Image"),
            available_online=True,
            archival_reference_code="HU OSA 300:2/7",
            title="Photo",
            archival_unit=SimpleNamespace(reference_code="HU OSA 300", title_full="Series title"),
            container=SimpleNamespace(container_no=2),
            folder_no=7,
        )

        factory = Mock()
        manifest = Mock()
        seq = Mock()
        canvas = Mock()

        factory.manifest.return_value = manifest
        manifest.sequence.return_value = seq
        seq.canvas.return_value = canvas
        manifest.toJSON.return_value = {"manifest": "ok"}

        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/FA-1/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_image_manifest_view.get_object_or_404",
            return_value=fa_entity,
        ), patch(
            "catalog.views.iiif_views.finding_aids_image_manifest_view.ManifestFactory",
            return_value=factory,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"manifest": "ok"})

        factory.set_base_prezi_uri.assert_called_once_with(
            "https://catalog.example/v1/catalog/finding-aids-image-manifest/FA-1/"
        )
        factory.set_base_image_uri.assert_called_once_with("https://images.example/iiif/2/")
        factory.set_iiif_image_info.assert_called_once_with(2.0, 2)
        factory.set_debug.assert_called_once_with("error")
        factory.manifest.assert_called_once_with(label="HU OSA 300:2/7 Photo")

        seq.canvas.assert_called_once_with(ident="Image", label="Image")
        canvas.set_image_annotation.assert_called_once_with(
            "catalog%2FHU_OSA_300%2FHU_OSA_300_0002_0007.jpg",
            iiif=True,
        )
        manifest.toJSON.assert_called_once_with(top=True)

    def test_get_returns_404_when_not_still_image_or_offline(self):
        fa_entity = SimpleNamespace(
            primary_type=SimpleNamespace(type="Audio"),
            available_online=False,
        )
        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/FA-2/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_image_manifest_view.get_object_or_404",
            return_value=fa_entity,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-2")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"Record is not an image, or not available online!"})

    def test_get_propagates_not_found(self):
        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/MISSING/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_image_manifest_view.get_object_or_404",
            side_effect=Http404,
        ):
            with self.assertRaises(Http404):
                self.view.get(request, fa_entity_catalog_id="MISSING")
