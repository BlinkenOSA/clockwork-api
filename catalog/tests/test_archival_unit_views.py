from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from catalog.views.archival_unit_views.archival_units_detail_view import (
    ArchivalUnitsDetailView,
    ArchivalUnitsFacetQuickView,
    ArchivalUnitsHelperView,
)
from isad.models import Isad


class ArchivalUnitsDetailViewTests(SimpleTestCase):
    def test_get_object_uses_archival_unit_id_and_published_filter(self):
        expected = SimpleNamespace(id=1)
        view = ArchivalUnitsDetailView()
        view.kwargs = {"archival_unit_id": "123"}

        with patch(
            "catalog.views.archival_unit_views.archival_units_detail_view.get_object_or_404",
            return_value=expected,
        ) as mock_get_object_or_404:
            result = view.get_object()

        self.assertIs(result, expected)
        mock_get_object_or_404.assert_called_once_with(
            Isad,
            archival_unit__id="123",
            published=True,
        )


class ArchivalUnitsFacetQuickViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_object_parses_reference_code_from_full_title(self):
        expected = SimpleNamespace(id=10)
        view = ArchivalUnitsFacetQuickView()
        view.request = Request(
            self.factory.get(
                "/v1/catalog/archival-units-facet-quick-view/",
                {"full_title": "HU OSA 300 - Sample title"},
            )
        )

        with patch(
            "catalog.views.archival_unit_views.archival_units_detail_view.get_object_or_404",
            return_value=expected,
        ) as mock_get_object_or_404:
            result = view.get_object()

        self.assertIs(result, expected)
        mock_get_object_or_404.assert_called_once_with(
            Isad,
            archival_unit__reference_code="HU OSA 300",
            published=True,
        )

    def test_get_object_without_full_title_raises_attribute_error(self):
        view = ArchivalUnitsFacetQuickView()
        view.request = Request(self.factory.get("/v1/catalog/archival-units-facet-quick-view/"))

        with self.assertRaises(AttributeError):
            view.get_object()


class ArchivalUnitsHelperViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_returns_catalog_id(self):
        request = self.factory.get("/v1/catalog/archival-units-helper/300/")
        view = ArchivalUnitsHelperView()

        with patch(
            "catalog.views.archival_unit_views.archival_units_detail_view.get_object_or_404",
            return_value=SimpleNamespace(catalog_id="CAT-123"),
        ) as mock_get_object_or_404:
            response = view.get(request, "300")

        self.assertEqual(response.data, {"catalog_id": "CAT-123"})
        mock_get_object_or_404.assert_called_once_with(
            Isad,
            reference_code="HU OSA 300",
            published=True,
        )
