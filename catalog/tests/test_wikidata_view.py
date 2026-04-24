from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from authority.models import Country
from catalog.views.facet_info_views.wikidata_view import WikidataView


class WikidataViewTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_returns_cached_payload_from_authority_record(self):
        payload = {
            "title": "Hungary",
            "description": "country in Central Europe",
            "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
            "properties": {"image": "https://img.test/hungary.jpg"},
        }
        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            Country.objects.create(
                alpha3="HUN",
                country="Hungary",
                wikidata_id="Q28",
                wikidata_cache=payload,
            )

        with patch("catalog.views.facet_info_views.wikidata_view.get_wikidata_entity_payload") as mock_get_payload:
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q28/"), wikidata_id="Q28")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, payload)
        mock_get_payload.assert_not_called()

    def test_get_fetches_live_payload_when_cache_missing_and_stores_it(self):
        payload = {
            "title": "Hungary",
            "description": "country in Central Europe",
            "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
            "properties": {"image": "https://img.test/hungary.jpg"},
        }
        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            country = Country.objects.create(
                alpha3="HUN",
                country="Hungary",
                wikidata_id="Q28",
            )

        with patch(
            "catalog.views.facet_info_views.wikidata_view.get_wikidata_entity_payload",
            return_value=payload,
        ) as mock_get_payload:
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q28/"), wikidata_id="Q28")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, payload)
        mock_get_payload.assert_called_once_with("Q28")

        country.refresh_from_db()
        self.assertEqual(country.wikidata_cache, payload)
        self.assertIsNotNone(country.wikidata_cache_updated_at)

    def test_get_returns_404_when_neither_cache_nor_live_payload_is_available(self):
        with patch(
            "catalog.views.facet_info_views.wikidata_view.get_wikidata_entity_payload",
            return_value=None,
        ):
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q0/"), wikidata_id="Q0")

        self.assertEqual(response.status_code, 404)

    def test_get_description_prefers_english_and_fallback(self):
        view = WikidataView()

        self.assertEqual(view._get_description({"en": "English", "fr": "Francais"}), "English")
        self.assertEqual(view._get_description({"fr": "Francais"}), "Francais")
