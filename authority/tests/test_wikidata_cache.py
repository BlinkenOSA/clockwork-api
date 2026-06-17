from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from authority.services.wikidata_cache import get_wikidata_entity_payload


class GetWikidataEntityPayloadTests(TestCase):
    @patch("authority.services.wikidata_cache.Client")
    def test_payload_includes_top_level_viaf_and_wikipedia_pages(self, mock_client_class):
        entity = SimpleNamespace(
            data={
                "claims": {
                    "P214": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": "12345678",
                                }
                            }
                        }
                    ]
                },
                "sitelinks": {
                    "enwiki": {"url": "https://en.wikipedia.org/wiki/Hungary"},
                    "huwiki": {"url": "https://hu.wikipedia.org/wiki/Magyarorsz%C3%A1g"},
                    "commonswiki": {"url": "https://commons.wikimedia.org/wiki/Hungary"},
                    "wikivoyage": {"url": "https://en.wikivoyage.org/wiki/Hungary"},
                },
            },
            label={"en": "Hungary"},
            description={"en": "country in Central Europe"},
        )
        mock_client = Mock()
        mock_client.get.return_value = entity
        mock_client_class.return_value = mock_client

        payload = get_wikidata_entity_payload("Q28")

        self.assertEqual(payload["viaf"], "12345678")
        self.assertEqual(payload["wikipedia"], "https://en.wikipedia.org/wiki/Hungary")
        self.assertEqual(
            payload["wikipedia_pages"],
            {
                "enwiki": "https://en.wikipedia.org/wiki/Hungary",
                "huwiki": "https://hu.wikipedia.org/wiki/Magyarorsz%C3%A1g",
            },
        )
        self.assertNotIn("viaf", payload["properties"])

    @patch("authority.services.wikidata_cache.Client")
    def test_payload_builds_wikipedia_urls_from_site_and_title_when_url_is_missing(self, mock_client_class):
        entity = SimpleNamespace(
            data={
                "claims": {},
                "sitelinks": {
                    "enwiki": {"site": "enwiki", "title": "Gyula Gazdag", "badges": []},
                    "frwiki": {"site": "frwiki", "title": "Gyula Gazdag", "badges": []},
                    "huwiki": {"site": "huwiki", "title": "Gazdag Gyula", "badges": []},
                    "wikivoyage": {"site": "wikivoyage", "title": "Gyula Gazdag", "badges": []},
                },
            },
            label={"en": "Gyula Gazdag"},
            description={"en": "Hungarian film director"},
        )
        mock_client = Mock()
        mock_client.get.return_value = entity
        mock_client_class.return_value = mock_client

        payload = get_wikidata_entity_payload("Q123")

        self.assertEqual(payload["wikipedia"], "https://en.wikipedia.org/wiki/Gyula_Gazdag")
        self.assertEqual(
            payload["wikipedia_pages"],
            {
                "enwiki": "https://en.wikipedia.org/wiki/Gyula_Gazdag",
                "frwiki": "https://fr.wikipedia.org/wiki/Gyula_Gazdag",
                "huwiki": "https://hu.wikipedia.org/wiki/Gazdag_Gyula",
            },
        )

    @patch("authority.services.wikidata_cache.get")
    @patch("authority.services.wikidata_cache.Client")
    def test_geoshape_is_saved_as_geojson(self, mock_client_class, mock_get):
        geojson = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "properties": {},
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[[1.0, 2.0], [3.0, 4.0], [1.0, 2.0]]],
                    },
                }
            ],
        }
        entity = SimpleNamespace(
            data={
                "claims": {
                    "P3896": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": "Data:Angola.map",
                                }
                            }
                        }
                    ]
                },
                "sitelinks": {},
            },
            label={"en": "Angola"},
            description={"en": "country in southwestern Africa"},
        )
        mock_client = Mock()
        mock_client.get.return_value = entity
        mock_client_class.return_value = mock_client

        response = Mock(status_code=200)
        response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "revisions": [
                            {
                                "slots": {
                                    "main": {
                                        "*": (
                                            '{"type": "FeatureCollection", "features": '
                                            '[{"type": "Feature", "properties": {}, '
                                            '"geometry": {"type": "Polygon", "coordinates": '
                                            '[[[1.0, 2.0], [3.0, 4.0], [1.0, 2.0]]]}}]}'
                                        )
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.return_value = response

        payload = get_wikidata_entity_payload("Q916")

        self.assertEqual(payload["properties"]["geoshape"], geojson)
        self.assertNotIn("geojson", payload["properties"])

    @patch("authority.services.wikidata_cache.time.sleep")
    @patch("authority.services.wikidata_cache.get")
    @patch("authority.services.wikidata_cache.Client")
    def test_geoshape_retries_after_transient_commons_failure(self, mock_client_class, mock_get, mock_sleep):
        entity = SimpleNamespace(
            data={
                "claims": {
                    "P3896": [
                        {
                            "mainsnak": {
                                "datavalue": {
                                    "value": "Data:Algeria.map",
                                }
                            }
                        }
                    ]
                },
                "sitelinks": {},
            },
            label={"en": "Algeria"},
            description={"en": "country in North Africa"},
        )
        mock_client = Mock()
        mock_client.get.return_value = entity
        mock_client_class.return_value = mock_client

        failed_response = Mock(status_code=503, text="maxlag")
        success_response = Mock(status_code=200)
        success_response.json.return_value = {
            "query": {
                "pages": {
                    "1": {
                        "revisions": [
                            {
                                "slots": {
                                    "main": {
                                        "*": '{"type": "FeatureCollection", "features": []}'
                                    }
                                }
                            }
                        ]
                    }
                }
            }
        }
        mock_get.side_effect = [failed_response, success_response]

        payload = get_wikidata_entity_payload("Q262")

        self.assertEqual(payload["properties"]["geoshape"], {"type": "FeatureCollection", "features": []})
        self.assertEqual(mock_get.call_count, 2)
        mock_sleep.assert_called_once_with(1.0)
