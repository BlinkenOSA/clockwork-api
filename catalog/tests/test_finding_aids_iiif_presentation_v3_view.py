from types import SimpleNamespace
from unittest.mock import Mock, patch

import requests
from django.http import Http404
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view import FindingAidsIIFPresentationV3View


class _DigitalVersionsManager:
    def __init__(self, versions):
        self.versions = list(versions)

    def all(self):
        return self

    def order_by(self, *args, **kwargs):
        return self.versions


class FindingAidsIIFPresentationV3ViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FindingAidsIIFPresentationV3View()

    @override_settings(BASE_URL="https://catalog.example", BASE_IMAGE_URI="https://images.example/iiif/2/")
    def test_get_builds_v3_manifest_and_skips_http_error_canvas(self):
        archival_unit = SimpleNamespace(title_full="Series title")
        digital_one = SimpleNamespace(identifier="AA_BB_CC_DD_EE_FF", filename="image 1.jpg", label="Page 1")
        digital_two = SimpleNamespace(identifier="GG_HH_II_JJ_KK_LL", filename="image2.jpg", label="")

        fa_entity = SimpleNamespace(
            primary_type=SimpleNamespace(type="Still Image"),
            available_online=True,
            archival_reference_code="HU OSA 1:1/1",
            title="Record title",
            archival_unit=archival_unit,
            digital_versions=_DigitalVersionsManager([digital_one, digital_two]),
        )

        manifest = Mock()
        canvas_ok = Mock()
        manifest.make_canvas_from_iiif.side_effect = [canvas_ok, requests.exceptions.HTTPError("bad iiif")]
        manifest.json.return_value = '{"ok": true}'

        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/FA-1/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view.get_object_or_404",
            return_value=fa_entity,
        ), patch(
            "catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view.Manifest",
            return_value=manifest,
        ) as mock_manifest_cls:
            response = self.view.get(request, fa_entity_catalog_id="FA-1")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True})

        mock_manifest_cls.assert_called_once_with(
            id="https://catalog.example/v1/catalog/finding-aids-image-manifest/FA-1/manifest.json",
            label="HU OSA 1:1/1 Record title<br/>Series title<br/>Blinken OSA Archivum",
        )

        self.assertEqual(manifest.make_canvas_from_iiif.call_count, 2)
        first_url = manifest.make_canvas_from_iiif.call_args_list[0].kwargs["url"]
        second_url = manifest.make_canvas_from_iiif.call_args_list[1].kwargs["url"]

        self.assertEqual(
            first_url,
            "https://images.example/iiif/2/catalog%2FAA_BB_CC_DD_EE%2Fimage+1.jpg",
        )
        self.assertEqual(
            second_url,
            "https://images.example/iiif/2/catalog%2FGG_HH_II_JJ_KK%2Fimage2.jpg",
        )

        canvas_ok.add_thumbnail.assert_called_once_with(
            image_url="https://images.example/iiif/2/catalog%2FAA_BB_CC_DD_EE%2Fimage+1.jpg/full/,300/0/default.jpg"
        )

    def test_get_returns_404_for_non_image_or_offline(self):
        fa_entity = SimpleNamespace(
            primary_type=SimpleNamespace(type="Audio"),
            available_online=False,
        )
        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/FA-2/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view.get_object_or_404",
            return_value=fa_entity,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-2")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.data, {"Record is not an image, or not available online!"})

    def test_get_propagates_not_found(self):
        request = self.factory.get("/v1/catalog/finding-aids-image-manifest/MISSING/manifest.json")

        with patch(
            "catalog.views.iiif_views.finding_aids_iiif_presentation_v3_view.get_object_or_404",
            side_effect=Http404,
        ):
            with self.assertRaises(Http404):
                self.view.get(request, fa_entity_catalog_id="MISSING")
