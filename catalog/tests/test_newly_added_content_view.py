from datetime import datetime
from types import SimpleNamespace
from unittest.mock import ANY, patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.statistics_views.newly_added_content import NewlyAddedContent


class _QS:
    def __init__(self, items):
        self.items = list(items)
        self.order_by_args = None

    def order_by(self, *args):
        self.order_by_args = args
        return self

    def all(self):
        return self.items


class _FAManager:
    def __init__(self, qs):
        self.qs = qs

    def select_related(self, *args):
        return self

    def filter(self, **kwargs):
        self.last_filter_kwargs = kwargs
        return self.qs


class NewlyAddedContentViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = NewlyAddedContent()

    def test_get_isad_returns_latest_five(self):
        isad_items = [
            SimpleNamespace(
                catalog_id=f"ISAD-{idx}",
                reference_code=f"HU OSA {idx}",
                archival_unit=SimpleNamespace(title_full=f"Title {idx}"),
                date_published=datetime(2026, 1, idx),
            )
            for idx in range(1, 7)
        ]
        qs = _QS(isad_items)

        with patch(
            "catalog.views.statistics_views.newly_added_content.Isad.objects.filter",
            return_value=qs,
        ) as mock_isad_filter:
            response = self.view.get(self.factory.get("/v1/catalog/newly-added-content/isad/"), content_type="isad")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual(response.data[0]["id"], "ISAD-1")
        self.assertEqual(response.data[-1]["id"], "ISAD-5")

        mock_isad_filter.assert_called_once_with(description_level="S", published=True)
        self.assertEqual(qs.order_by_args, ("-date_published",))

    def test_get_non_isad_returns_max_five_unique_series(self):
        series_1 = SimpleNamespace(
            id=101,
            isad=SimpleNamespace(catalog_id="ISAD-101"),
            reference_code="HU OSA 101",
            title_full="Series 101",
        )
        series_2 = SimpleNamespace(
            id=102,
            isad=SimpleNamespace(catalog_id="ISAD-102"),
            reference_code="HU OSA 102",
            title_full="Series 102",
        )
        series_3 = SimpleNamespace(
            id=103,
            isad=SimpleNamespace(catalog_id="ISAD-103"),
            reference_code="HU OSA 103",
            title_full="Series 103",
        )
        series_4 = SimpleNamespace(
            id=104,
            isad=SimpleNamespace(catalog_id="ISAD-104"),
            reference_code="HU OSA 104",
            title_full="Series 104",
        )
        series_5 = SimpleNamespace(
            id=105,
            isad=SimpleNamespace(catalog_id="ISAD-105"),
            reference_code="HU OSA 105",
            title_full="Series 105",
        )
        series_6 = SimpleNamespace(
            id=106,
            isad=SimpleNamespace(catalog_id="ISAD-106"),
            reference_code="HU OSA 106",
            title_full="Series 106",
        )

        fa_items = [
            SimpleNamespace(archival_unit=series_1, date_published=datetime(2026, 2, 1)),
            SimpleNamespace(archival_unit=series_1, date_published=datetime(2026, 2, 2)),
            SimpleNamespace(archival_unit=series_2, date_published=datetime(2026, 2, 3)),
            SimpleNamespace(archival_unit=series_3, date_published=datetime(2026, 2, 4)),
            SimpleNamespace(archival_unit=series_4, date_published=datetime(2026, 2, 5)),
            SimpleNamespace(archival_unit=series_5, date_published=datetime(2026, 2, 6)),
            SimpleNamespace(archival_unit=series_6, date_published=datetime(2026, 2, 7)),
        ]

        qs = _QS(fa_items)
        manager = _FAManager(qs)

        with patch(
            "catalog.views.statistics_views.newly_added_content.FindingAidsEntity.objects",
            manager,
        ):
            response = self.view.get(self.factory.get("/v1/catalog/newly-added-content/folder/"), content_type="folder")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 5)
        self.assertEqual([row["id"] for row in response.data], ["ISAD-101", "ISAD-102", "ISAD-103", "ISAD-104", "ISAD-105"])

        self.assertEqual(qs.order_by_args, ("-date_published",))
        self.assertEqual(manager.last_filter_kwargs["published"], True)
        self.assertEqual(manager.last_filter_kwargs["date_published__year__gt"], ANY)
