from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

from authority.services.wikidata_cache import get_wikidata_entity_payload


class GetWikidataEntityPayloadTests(TestCase):
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
