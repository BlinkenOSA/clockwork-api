from types import SimpleNamespace
from unittest.mock import patch

from django.http import Http404
from django.test import SimpleTestCase

from catalog.serializers.archival_units_tree_quick_view_serializer import ArchivalUnitsTreeQuickViewSerializer
from catalog.views.tree_views.archival_units_tree_quick_view import ArchivalUnitsTreeQuickView
from isad.models import Isad


class ArchivalUnitsTreeQuickViewTests(SimpleTestCase):
    def test_view_configuration(self):
        self.assertEqual(ArchivalUnitsTreeQuickView.permission_classes, [])
        self.assertIs(ArchivalUnitsTreeQuickView.serializer_class, ArchivalUnitsTreeQuickViewSerializer)

    def test_get_object_uses_archival_unit_id_and_published_filter(self):
        expected = SimpleNamespace(id=123)
        view = ArchivalUnitsTreeQuickView()
        view.kwargs = {"archival_unit_id": "42"}

        with patch(
            "catalog.views.tree_views.archival_units_tree_quick_view.get_object_or_404",
            return_value=expected,
        ) as mock_get_object_or_404:
            result = view.get_object()

        self.assertIs(result, expected)
        mock_get_object_or_404.assert_called_once_with(
            Isad,
            archival_unit__id="42",
            published=True,
        )

    def test_get_object_propagates_not_found(self):
        view = ArchivalUnitsTreeQuickView()
        view.kwargs = {"archival_unit_id": "missing"}

        with patch(
            "catalog.views.tree_views.archival_units_tree_quick_view.get_object_or_404",
            side_effect=Http404,
        ):
            with self.assertRaises(Http404):
                view.get_object()
