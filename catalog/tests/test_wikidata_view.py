import json
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from requests.exceptions import RequestException
from rest_framework.test import APIRequestFactory

from catalog.views.facet_info_views.wikidata_view import WikidataView


class WikidataViewTests(SimpleTestCase):
    def setUp(self):
        self.factory = APIRequestFactory()

    def test_get_returns_404_when_entity_data_missing(self):
        entity = SimpleNamespace(data={}, label={"en": "N/A"}, description={"en": "N/A"})
        client = SimpleNamespace(get=Mock(return_value=entity))

        with patch("catalog.views.facet_info_views.wikidata_view.Client", return_value=client):
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q0/"), wikidata_id="Q0")

        self.assertEqual(response.status_code, 404)

    def test_get_returns_curated_wikidata_payload(self):
        entity = SimpleNamespace(
            data={
                "claims": {
                    "P17": [{"mainsnak": {"datavalue": {"value": {"id": "QCOUNTRY"}}}, "rank": "normal"}],
                    "P18": [{"mainsnak": {"datavalue": {"value": "My File.jpg"}}}],
                    "P625": [{"mainsnak": {"datavalue": {"value": {"latitude": 47.5, "longitude": 19.0}}}}],
                    "P569": [{"mainsnak": {"datavalue": {"value": {"time": "+1870-01-01T00:00:00Z"}}}}],
                    "P106": [{"mainsnak": {"datavalue": {"value": {"id": "QOCC"}}}}],
                    "P800": [{"mainsnak": {"datavalue": {"value": {"id": "QWORK"}}}}],
                    "P3896": [{"mainsnak": {"datavalue": {"value": "Data:Geo.map"}}}],
                    "P19": [{"mainsnak": {"datavalue": {"value": {"id": "QBIRTH"}}}}],
                },
                "sitelinks": {
                    "huwiki": {"url": "https://hu.wikipedia.org/wiki/Pelda"},
                    "dewiki": {"url": "https://de.wikipedia.org/wiki/Beispiel"},
                },
            },
            label={"en": "John Doe"},
            description={"fr": "Description francaise"},
        )

        properties = {
            "QCOUNTRY": SimpleNamespace(label={"en": "Hungary"}),
            "QOCC": SimpleNamespace(label={"en": "Historian"}),
            "QWORK": SimpleNamespace(label={"en": "Major Work"}),
            "QBIRTH": SimpleNamespace(label={"en": "Budapest"}),
        }

        def _client_get(value, load=True):
            if value == "Q123":
                return entity
            return properties[value]

        client = SimpleNamespace(get=Mock(side_effect=_client_get))

        image_response = SimpleNamespace(
            status_code=200,
            json=lambda: {"query": {"pages": {"1": {"imageinfo": [{"url": "https://img.test/file.jpg"}]}}}},
        )
        geojson_payload = {"type": "FeatureCollection", "features": []}
        geoshape_response = SimpleNamespace(
            status_code=200,
            json=lambda: {
                "query": {"pages": {"1": {"revisions": [{"*": json.dumps(geojson_payload)}]}}}
            },
        )

        with patch("catalog.views.facet_info_views.wikidata_view.Client", return_value=client), patch(
            "catalog.views.facet_info_views.wikidata_view.get",
            side_effect=[image_response, geoshape_response],
        ):
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q123/"), wikidata_id="Q123")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "John Doe")
        self.assertEqual(response.data["description"], "Description francaise")
        self.assertEqual(response.data["wikipedia"], "https://hu.wikipedia.org/wiki/Pelda")

        props = response.data["properties"]
        self.assertEqual(props["country"], "Hungary")
        self.assertEqual(props["image"], "https://img.test/file.jpg")
        self.assertEqual(props["coordinates"], {"lat": 47.5, "long": 19.0})
        self.assertEqual(props["date_of_birth"], "+1870-01-01T00:00:00Z")
        self.assertEqual(props["occupation"], ["Historian"])
        self.assertEqual(props["notable_work"], ["Major Work"])
        self.assertEqual(props["geoshape"], "https://commons.wikimedia.org/wiki/Data:Geo.map")
        self.assertEqual(props["geojson"], geojson_payload)
        self.assertEqual(props["place_of_birth"], "Budapest")

    def test_get_handles_image_request_exception(self):
        entity = SimpleNamespace(
            data={
                "claims": {"P18": [{"mainsnak": {"datavalue": {"value": "Missing File.jpg"}}}]},
                "sitelinks": {},
            },
            label={"en": "John Doe"},
            description={"en": "English description"},
        )
        client = SimpleNamespace(get=Mock(return_value=entity))

        with patch("catalog.views.facet_info_views.wikidata_view.Client", return_value=client), patch(
            "catalog.views.facet_info_views.wikidata_view.get",
            side_effect=RequestException("network error"),
        ):
            response = WikidataView.as_view()(self.factory.get("/v1/catalog/wikidata/Q9/"), wikidata_id="Q9")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["title"], "John Doe")
        self.assertEqual(response.data["description"], "English description")
        self.assertEqual(response.data["wikipedia"], "")
        self.assertNotIn("image", response.data["properties"])

    def test_get_description_prefers_english_and_fallback(self):
        view = WikidataView()

        self.assertEqual(view._get_description({"en": "English", "fr": "Francais"}), "English")
        self.assertEqual(view._get_description({"fr": "Francais"}), "Francais")
