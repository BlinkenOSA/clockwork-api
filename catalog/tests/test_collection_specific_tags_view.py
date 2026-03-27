from unittest.mock import patch

from django.test import SimpleTestCase
from rest_framework.test import APIRequestFactory

from catalog.views.statistics_views.collection_specific_tags import CollectionSpecificTags


class _KeywordObj:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class _KeywordQS:
    def __init__(self, items):
        self._items = list(items)
        self.order_by_called_with = None
        self.distinct_called = False

    def order_by(self, value):
        self.order_by_called_with = value
        return self

    def distinct(self):
        self.distinct_called = True
        return self

    def __iter__(self):
        return iter(self._items)


class CollectionSpecificTagsViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = CollectionSpecificTags()

    def test_get_returns_empty_list(self):
        qs = _KeywordQS([])

        with patch(
            "catalog.views.statistics_views.collection_specific_tags.Keyword.objects.filter",
            return_value=qs,
        ) as mock_filter:
            response = self.view.get(self.factory.get("/v1/catalog/collection-specific-tags/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])
        mock_filter.assert_called_once_with(findingaidsentity__published=True)
        self.assertEqual(qs.order_by_called_with, "?")
        self.assertTrue(qs.distinct_called)

    def test_get_deduplicates_and_limits_to_ten(self):
        values = [
            "tag-1",
            "tag-2",
            "tag-2",
            "tag-3",
            "tag-4",
            "tag-5",
            "tag-6",
            "tag-7",
            "tag-8",
            "tag-9",
            "tag-10",
            "tag-11",
            "tag-12",
        ]
        qs = _KeywordQS([_KeywordObj(v) for v in values])

        with patch(
            "catalog.views.statistics_views.collection_specific_tags.Keyword.objects.filter",
            return_value=qs,
        ):
            response = self.view.get(self.factory.get("/v1/catalog/collection-specific-tags/"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.data,
            [
                "tag-1",
                "tag-2",
                "tag-3",
                "tag-4",
                "tag-5",
                "tag-6",
                "tag-7",
                "tag-8",
                "tag-9",
                "tag-10",
            ],
        )
