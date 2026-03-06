from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.tree_views.archival_units_tree_view import ArchivalUnitsTreeView


class _ValuesQS:
    def __init__(self, rows):
        self.rows = list(rows)

    def __iter__(self):
        return iter(self.rows)

    def count(self):
        return len(self.rows)

    def values(self, *fields):
        return [{field: row.get(field) for field in fields} for row in self.rows]


class _ArchivalUnitQS:
    def __init__(self, rows):
        self.rows = list(rows)

    def select_related(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def values(self, *fields):
        projected = [{field: row.get(field) for field in fields} for row in self.rows]
        return _ValuesQS(projected)


class _SeriesNode(dict):
    pass


class ArchivalUnitsTreeViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = ArchivalUnitsTreeView()

    def test_get_themes_builds_theme_map(self):
        qs = _ValuesQS([
            {"id": 1, "theme": "A"},
            {"id": 1, "theme": "B"},
            {"id": 2, "theme": "C"},
        ])

        self.view.get_themes(qs)

        self.assertEqual(self.view.themes, {1: ["A", "B"], 2: ["C"]})

    def test_get_unit_data_uses_preloaded_themes(self):
        self.view.themes = {5: ["theme-x"]}
        au = {
            "id": 5,
            "isad__catalog_id": "ISAD-5",
            "reference_code": "HU OSA 5",
            "title": "Title",
            "title_original": "Original",
            "level": "S",
        }

        data = self.view.get_unit_data(au)

        self.assertEqual(data["catalog_id"], "ISAD-5")
        self.assertEqual(data["key"], "hu_osa_5")
        self.assertEqual(data["themes"], ["theme-x"])
        self.assertEqual(data["children"], [])

    def test_has_online_content_for_f_and_sf(self):
        fa_qs_f = object()
        fa_qs_sf = object()
        dv_qs_f = SimpleNamespace(count=Mock(return_value=4))
        dv_qs_sf = SimpleNamespace(count=Mock(return_value=2))

        with patch(
            "catalog.views.tree_views.archival_units_tree_view.FindingAidsEntity.objects.filter",
            side_effect=[fa_qs_f, fa_qs_sf],
        ) as mock_fa_filter, patch(
            "catalog.views.tree_views.archival_units_tree_view.DigitalVersion.objects.filter",
            side_effect=[dv_qs_f, dv_qs_sf],
        ) as mock_dv_filter:
            count_f = self.view.has_online_content({"level": "F", "id": 10})
            count_sf = self.view.has_online_content({"level": "SF", "id": 20})

        self.assertEqual(count_f, 4)
        self.assertEqual(count_sf, 2)

        self.assertEqual(mock_fa_filter.call_count, 2)
        self.assertEqual(mock_dv_filter.call_count, 2)

    def test_has_online_content_for_series(self):
        fa_all = ["fa1", "fa2"]
        series = _SeriesNode({"level": "S"})
        series.findingaidsentity_set = SimpleNamespace(all=Mock(return_value=fa_all))

        dv_qs = SimpleNamespace(count=Mock(return_value=7))
        with patch(
            "catalog.views.tree_views.archival_units_tree_view.DigitalVersion.objects.filter",
            return_value=dv_qs,
        ) as mock_dv_filter:
            count_s = self.view.has_online_content(series)

        self.assertEqual(count_s, 7)
        mock_dv_filter.assert_called_once_with(
            finding_aids_entity__in=fa_all,
            finding_aids_entity__published=True,
            available_online=True,
        )

    def test_get_all_theme_filtered_builds_tree(self):
        rows = [
            {
                "id": 1,
                "fonds": 1,
                "subfonds": 0,
                "series": 0,
                "reference_code": "HU OSA 100",
                "title": "Fonds",
                "title_original": "Fonds Orig",
                "level": "F",
                "isad__catalog_id": "ISAD-F",
            },
            {
                "id": 2,
                "fonds": 1,
                "subfonds": 1,
                "series": 0,
                "reference_code": "HU OSA 100/1",
                "title": "Subfonds",
                "title_original": "Subfonds Orig",
                "level": "SF",
                "isad__catalog_id": "ISAD-SF",
            },
            {
                "id": 3,
                "fonds": 1,
                "subfonds": 1,
                "series": 1,
                "reference_code": "HU OSA 100/1/1",
                "title": "Series A",
                "title_original": "Series A Orig",
                "level": "S",
                "isad__catalog_id": "ISAD-S1",
            },
            {
                "id": 4,
                "fonds": 1,
                "subfonds": 0,
                "series": 2,
                "reference_code": "HU OSA 100/2",
                "title": "Series B",
                "title_original": "Series B Orig",
                "level": "S",
                "isad__catalog_id": "ISAD-S2",
            },
        ]
        for row in rows:
            row["theme"] = "theme-a"

        qs = _ArchivalUnitQS(rows)
        request = self.factory.get("/v1/catalog/archival-units-tree/all/theme-a/")

        with patch(
            "catalog.views.tree_views.archival_units_tree_view.ArchivalUnit.objects.filter",
            return_value=qs,
        ) as mock_filter:
            response = self.view.get(request, archival_unit_id="all", theme="theme-a")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        fonds = response.data[0]
        self.assertEqual(fonds["level"], "F")
        self.assertEqual(len(fonds["children"]), 2)

        subfonds = [node for node in fonds["children"] if node["level"] == "SF"][0]
        self.assertEqual(len(subfonds["children"]), 1)
        self.assertTrue(subfonds["children"][0]["subfonds"])

        direct_series = [node for node in fonds["children"] if node["level"] == "S"][0]
        self.assertFalse(direct_series["subfonds"])

        mock_filter.assert_called_once_with(isad__published=True, theme__id="theme-a")

    def test_get_specific_archival_unit_scopes_by_fonds(self):
        rows = [
            {
                "id": 11,
                "fonds": 9,
                "subfonds": 0,
                "series": 0,
                "reference_code": "HU OSA 900",
                "title": "Scoped Fonds",
                "title_original": "Scoped Fonds Orig",
                "level": "F",
                "isad__catalog_id": "ISAD-900",
                "theme": "t1",
            }
        ]
        qs = _ArchivalUnitQS(rows)
        archival_unit = SimpleNamespace(fonds=9)
        request = self.factory.get("/v1/catalog/archival-units-tree/11/")

        with patch(
            "catalog.views.tree_views.archival_units_tree_view.get_object_or_404",
            return_value=archival_unit,
        ) as mock_get_object_or_404, patch(
            "catalog.views.tree_views.archival_units_tree_view.ArchivalUnit.objects.filter",
            return_value=qs,
        ) as mock_filter:
            response = self.view.get(request, archival_unit_id="11", theme=None)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], 11)

        mock_get_object_or_404.assert_called_once()
        mock_filter.assert_called_once_with(isad__published=True, fonds=9)
