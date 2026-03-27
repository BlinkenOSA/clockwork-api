from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.finding_aids_views.finding_aids_entity_location_view import FindingAidsEntityLocationView


class _FakeFAQuerySet:
    def __init__(self, items, count_value=None):
        self.items = list(items)
        self._count_value = count_value if count_value is not None else len(self.items)

    def order_by(self, *args, **kwargs):
        return self

    def count(self):
        return self._count_value

    def first(self):
        return self.items[0] if self.items else None

    def last(self):
        return self.items[-1] if self.items else None

    def filter(self, **kwargs):
        if "folder_no" in kwargs:
            folder_no = kwargs["folder_no"]
            filtered = [item for item in self.items if getattr(item, "folder_no", None) == folder_no]
            return _FakeFAQuerySet(filtered, count_value=len(filtered))
        return _FakeFAQuerySet(self.items, count_value=self._count_value)


class FindingAidsEntityLocationViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = FindingAidsEntityLocationView()

    def _build_hierarchy(self):
        fonds = SimpleNamespace(
            id=1,
            isad=SimpleNamespace(catalog_id="ISAD-F"),
            reference_code="HU OSA 100",
            title="Fonds",
            title_original="Fonds Original",
            level="F",
            subfonds=1,
        )
        subfonds = SimpleNamespace(
            id=2,
            isad=SimpleNamespace(catalog_id="ISAD-SF"),
            reference_code="HU OSA 100 1",
            title="Subfonds",
            title_original="Subfonds Original",
            level="SF",
            subfonds=1,
            parent=fonds,
        )
        series = SimpleNamespace(
            id=3,
            isad=SimpleNamespace(catalog_id="ISAD-S"),
            reference_code="HU OSA 100 1 1",
            title="Series",
            title_original="Series Original",
            level="S",
            subfonds=1,
            parent=subfonds,
        )
        container = SimpleNamespace(
            archival_unit=series,
            container_no=5,
            carrier_type=SimpleNamespace(type="Box"),
        )
        return fonds, subfonds, series, container

    def _build_fa(self, series, container, folder_no, archival_reference_code, catalog_id, level="F", description_level="L1"):
        return SimpleNamespace(
            catalog_id=catalog_id,
            archival_reference_code=archival_reference_code,
            title=f"Title {folder_no}",
            level=level,
            archival_unit=series,
            container=container,
            description_level=description_level,
            folder_no=folder_no,
        )

    def test_helper_serializers(self):
        _, _, series, container = self._build_hierarchy()
        fa_folder = self._build_fa(series, container, 1, "HU OSA 100:5/1", "FA-1", level="F")
        fa_item = self._build_fa(series, container, 2, "HU OSA 100:5/2-1", "FA-2", level="I")

        au_data = self.view.get_archival_unit_data(series)
        self.assertEqual(au_data["id"], 3)
        self.assertEqual(au_data["catalog_id"], "ISAD-S")
        self.assertEqual(au_data["key"], "hu_osa_100_1_1")

        placeholder = self.view.get_placeholder("folder", True)
        self.assertEqual(placeholder, {"key": "placeholder", "level": "folder", "has_subfonds": True})

        container_data = self.view.get_container_data(container)
        self.assertEqual(container_data["key"], "hu_osa_100_1_1_5")
        self.assertEqual(container_data["reference_code"], "HU OSA 100 1 1:5")
        self.assertEqual(container_data["carrier_type"], "Box")

        folder_data = self.view.get_fa_entity_data(fa_folder, active=True)
        item_data = self.view.get_fa_entity_data(fa_item, active=False)
        self.assertEqual(folder_data["level"], "folder")
        self.assertTrue(folder_data["active"])
        self.assertEqual(item_data["level"], "item")
        self.assertFalse(item_data["active"])

    def test_get_non_l1_returns_hierarchy_and_container_only(self):
        _, _, series, container = self._build_hierarchy()
        fa_entity = self._build_fa(
            series,
            container,
            folder_no=1,
            archival_reference_code="HU OSA 100:5/1",
            catalog_id="FA-ACTIVE",
            description_level="L2",
        )

        request = self.factory.get("/v1/catalog/finding-aids-location/FA-ACTIVE/")
        with patch(
            "catalog.views.finding_aids_views.finding_aids_entity_location_view.get_object_or_404",
            return_value=fa_entity,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-ACTIVE")

        self.assertEqual(len(response.data), 4)
        self.assertEqual(response.data[0]["level"], "F")
        self.assertEqual(response.data[1]["level"], "SF")
        self.assertEqual(response.data[2]["level"], "S")
        self.assertEqual(response.data[3]["level"], "container")

    def test_get_l1_adds_context_nodes_including_placeholders(self):
        _, _, series, container = self._build_hierarchy()

        fa_first = self._build_fa(series, container, 1, "HU OSA 100:5/1", "FA-1")
        fa_previous = self._build_fa(series, container, 3, "HU OSA 100:5/3", "FA-3")
        fa_active = self._build_fa(series, container, 4, "HU OSA 100:5/4", "FA-4")
        fa_next = self._build_fa(series, container, 5, "HU OSA 100:5/5", "FA-5")
        fa_last = self._build_fa(series, container, 7, "HU OSA 100:5/7", "FA-7")
        qs = _FakeFAQuerySet([fa_first, fa_previous, fa_active, fa_next, fa_last], count_value=7)

        request = self.factory.get("/v1/catalog/finding-aids-location/FA-4/")
        with patch(
            "catalog.views.finding_aids_views.finding_aids_entity_location_view.get_object_or_404",
            return_value=fa_active,
        ), patch(
            "catalog.views.finding_aids_views.finding_aids_entity_location_view.FindingAidsEntity.objects.filter",
            return_value=qs,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-4")

        levels = [node["level"] for node in response.data]
        self.assertEqual(levels[:4], ["F", "SF", "S", "container"])

        placeholders = [node for node in response.data if node.get("key") == "placeholder"]
        self.assertEqual(len(placeholders), 2)

        active_nodes = [node for node in response.data if node.get("active")]
        self.assertEqual(len(active_nodes), 1)
        self.assertEqual(active_nodes[0]["catalog_id"], "FA-4")

    def test_get_skips_archival_units_without_isad_attribute(self):
        fonds = SimpleNamespace()
        subfonds = SimpleNamespace(parent=fonds)
        series = SimpleNamespace(parent=subfonds, subfonds=0, reference_code="HU OSA 200")
        container = SimpleNamespace(
            archival_unit=series,
            container_no=1,
            carrier_type=SimpleNamespace(type="Box"),
        )
        fa_entity = SimpleNamespace(
            catalog_id="FA-MIN",
            archival_reference_code="HU OSA 200:1/1",
            title="Minimal",
            level="F",
            archival_unit=series,
            container=container,
            description_level="L2",
            folder_no=1,
        )

        request = self.factory.get("/v1/catalog/finding-aids-location/FA-MIN/")
        with patch(
            "catalog.views.finding_aids_views.finding_aids_entity_location_view.get_object_or_404",
            return_value=fa_entity,
        ):
            response = self.view.get(request, fa_entity_catalog_id="FA-MIN")

        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["level"], "container")
