from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.http import Http404
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIRequestFactory

from catalog.views.iiif_views.archival_units_image_manifest_view import ArchivalUnitsManifestView


class ArchivalUnitsManifestViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ArchivalUnitsManifestView()

    @override_settings(BASE_URL="https://catalog.example")
    def test_get_builds_manifest_and_adds_only_still_images(self):
        archival_unit = SimpleNamespace(title_full="Series Title", reference_code="HU OSA 123")
        isad = SimpleNamespace(archival_unit=archival_unit)

        still_image = SimpleNamespace(
            primary_type=SimpleNamespace(type="Still Image"),
            archival_unit=archival_unit,
            container=SimpleNamespace(container_no=2),
            folder_no=7,
            archival_reference_code="HU OSA 123:2/7",
            title="Photo",
        )
        non_still = SimpleNamespace(
            primary_type=SimpleNamespace(type="Audio"),
            archival_unit=archival_unit,
            container=SimpleNamespace(container_no=9),
            folder_no=1,
            archival_reference_code="HU OSA 123:9/1",
            title="Tape",
        )

        factory = Mock()
        manifest = Mock()
        seq = Mock()
        canvas = Mock()
        factory.manifest.return_value = manifest
        manifest.sequence.return_value = seq
        seq.canvas.return_value = canvas
        manifest.toJSON.return_value = {"manifest": "ok"}

        request = self.factory.get("/v1/catalog/archival-units-image-manifest/10/manifest.json")

        with patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.get_object_or_404",
            return_value=isad,
        ) as mock_get_object_or_404, patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.ManifestFactory",
            return_value=factory,
        ), patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.FindingAidsEntity.objects.filter",
            return_value=[still_image, non_still],
        ) as mock_fa_filter:
            response = self.view.get(request, archival_unit_id="10")

        self.assertEqual(response.data, {"manifest": "ok"})

        mock_get_object_or_404.assert_called_once()
        mock_fa_filter.assert_called_once_with(archival_unit=archival_unit, digital_version_online=True)

        factory.set_base_prezi_uri.assert_called_once_with(
            "https://catalog.example/v1/catalog/archival-units-image-manifest/10/manifest.json"
        )
        factory.set_base_image_uri.assert_called_once()
        factory.set_iiif_image_info.assert_called_once_with(2.0, 2)
        factory.set_debug.assert_called_once_with("error")
        factory.manifest.assert_called_once_with(label="Series Title")

        seq.canvas.assert_called_once_with(ident="HU OSA 123:2/7", label="HU OSA 123:2/7 Photo")
        canvas.set_image_annotation.assert_called_once_with(
            "catalog%2FHU_OSA_123%2FHU_OSA_123-0002-007.jpg",
            iiif=True,
        )

    @override_settings(BASE_URL="https://catalog.example")
    def test_get_returns_manifest_even_when_no_still_images(self):
        archival_unit = SimpleNamespace(title_full="Series Title", reference_code="HU OSA 999")
        isad = SimpleNamespace(archival_unit=archival_unit)

        non_still = SimpleNamespace(
            primary_type=SimpleNamespace(type="Video"),
            archival_unit=archival_unit,
            container=SimpleNamespace(container_no=1),
            folder_no=1,
            archival_reference_code="HU OSA 999:1/1",
            title="Movie",
        )

        factory = Mock()
        manifest = Mock()
        seq = Mock()
        factory.manifest.return_value = manifest
        manifest.sequence.return_value = seq
        manifest.toJSON.return_value = {"manifest": "empty"}

        request = self.factory.get("/v1/catalog/archival-units-image-manifest/99/manifest.json")

        with patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.get_object_or_404",
            return_value=isad,
        ), patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.ManifestFactory",
            return_value=factory,
        ), patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.FindingAidsEntity.objects.filter",
            return_value=[non_still],
        ):
            response = self.view.get(request, archival_unit_id="99")

        self.assertEqual(response.data, {"manifest": "empty"})
        seq.canvas.assert_not_called()

    def test_get_propagates_not_found(self):
        request = self.factory.get("/v1/catalog/archival-units-image-manifest/404/manifest.json")

        with patch(
            "catalog.views.iiif_views.archival_units_image_manifest_view.get_object_or_404",
            side_effect=Http404,
        ):
            with self.assertRaises(Http404):
                self.view.get(request, archival_unit_id="404")
