from types import SimpleNamespace
from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.statistics_views.archival_unit_sizes import ArchivalUnitSizes


class ArchivalUnitSizesViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ArchivalUnitSizes()

    def test_get_returns_empty_list_when_no_fonds(self):
        fonds_qs = SimpleNamespace(all=lambda: [])

        with patch(
            "catalog.views.statistics_views.archival_unit_sizes.ArchivalUnit.objects.filter",
            return_value=fonds_qs,
        ) as mock_au_filter:
            response = self.view.get(self.factory.get("/v1/catalog/archival-unit-sizes/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        mock_au_filter.assert_called_once_with(level="F", isad__published=True)

    def test_get_returns_size_per_fonds(self):
        fonds_1 = SimpleNamespace(reference_code="HU OSA 100", title="Fonds One")
        fonds_2 = SimpleNamespace(reference_code="HU OSA 200", title="Fonds Two")
        fonds_qs = SimpleNamespace(all=lambda: [fonds_1, fonds_2])

        count_qs_1 = Mock()
        count_qs_1.count.return_value = 12
        count_qs_2 = Mock()
        count_qs_2.count.return_value = 3

        with patch(
            "catalog.views.statistics_views.archival_unit_sizes.ArchivalUnit.objects.filter",
            return_value=fonds_qs,
        ), patch(
            "catalog.views.statistics_views.archival_unit_sizes.FindingAidsEntity.objects.filter",
            side_effect=[count_qs_1, count_qs_2],
        ) as mock_fa_filter:
            response = self.view.get(self.factory.get("/v1/catalog/archival-unit-sizes/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [
                {"reference_code": "HU OSA 100", "title": "Fonds One", "size": 12},
                {"reference_code": "HU OSA 200", "title": "Fonds Two", "size": 3},
            ],
        )

        self.assertEqual(
            mock_fa_filter.call_args_list,
            [
                call(archival_unit__parent__parent=fonds_1, published=True),
                call(archival_unit__parent__parent=fonds_2, published=True),
            ],
        )
