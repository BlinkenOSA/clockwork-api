from types import SimpleNamespace
from unittest.mock import patch

from django.http import Http404
from django.test import SimpleTestCase

from catalog.views.finding_aids_views.finding_aids_entity_detail_view import FindingAidsEntityDetailView
from finding_aids.models import FindingAidsEntity


class FindingAidsEntityDetailViewTests(SimpleTestCase):
    def test_get_object_uses_catalog_id_and_published_filter(self):
        expected = SimpleNamespace(id=55)
        view = FindingAidsEntityDetailView()
        view.kwargs = {"fa_entity_catalog_id": "FA-12345"}

        with patch(
            "catalog.views.finding_aids_views.finding_aids_entity_detail_view.get_object_or_404",
            return_value=expected,
        ) as mock_get_object_or_404:
            result = view.get_object()

        self.assertIs(result, expected)
        mock_get_object_or_404.assert_called_once_with(
            FindingAidsEntity,
            catalog_id="FA-12345",
            published=True,
        )

    def test_get_object_propagates_not_found(self):
        view = FindingAidsEntityDetailView()
        view.kwargs = {"fa_entity_catalog_id": "MISSING"}

        with patch(
            "catalog.views.finding_aids_views.finding_aids_entity_detail_view.get_object_or_404",
            side_effect=Http404,
        ):
            with self.assertRaises(Http404):
                view.get_object()
