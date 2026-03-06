import json
from unittest.mock import Mock, patch

from django.test import TestCase

from authority.views.lcsh_views import LCSHMixin
from authority.views.viaf_views import VIAFMixin
from authority.views.wikidata_views import WikidataMixin
from authority.views.wikipedia_views import WikipediaMixin


class LCSHMixinTests(TestCase):
    def test_empty_query_returns_empty(self):
        mixin = LCSHMixin()
        self.assertEqual(mixin.get_lcshlinks("", "genre"), [])

    def test_parses_lcsh_response(self):
        mixin = LCSHMixin()
        payload = [
            [
                "atom:entry",
                0,
                [None, None, "Label"],
                [None, {"href": "http://id.loc.gov/authorities/subjects/sh1"}],
            ]
        ]
        mock_response = Mock(status_code=200, text=json.dumps(payload))
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.close.return_value = None

        with patch("authority.views.lcsh_views.Session", return_value=mock_session):
            data = mixin.get_lcshlinks("Human Rights", "subject")

        self.assertEqual(data[0]["lcsh_id"], "http://id.loc.gov/authorities/subjects/sh1")


class WikidataMixinTests(TestCase):
    def test_parses_wikidata_response(self):
        mixin = WikidataMixin()
        payload = {
            "query": {
                "searchinfo": {"totalhits": 1},
                "search": [
                    {
                        "title": "Q42",
                        "titlesnippet": "Douglas Adams",
                        "snippet": "writer",
                    }
                ],
            }
        }
        mock_response = Mock(status_code=200, text=json.dumps(payload))
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.close.return_value = None

        with patch("authority.views.wikidata_views.Session", return_value=mock_session):
            data = mixin.get_wikidata_links("Douglas Adams")

        self.assertEqual(data[0]["wikidata_id"], "Q42")
        self.assertEqual(data[0]["wikidata_url"], "https://www.wikidata.org/wiki/Q42")


class VIAFMixinTests(TestCase):
    def test_parses_viaf_response_single_record(self):
        mixin = VIAFMixin()
        payload = {
            "searchRetrieveResponse": {
                "records": {
                    "record": {
                        "recordData": {
                            "ns2:VIAFCluster": {
                                "ns2:viafID": "123",
                                "ns2:mainHeadings": {
                                    "ns2:data": {"ns2:text": "Test Name"}
                                },
                            }
                        }
                    }
                }
            }
        }
        mock_response = Mock(status_code=200, text=json.dumps(payload))
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.close.return_value = None

        with patch("authority.views.viaf_views.Session", return_value=mock_session):
            data = mixin.get_results_from_viaf("Test", "person")

        self.assertEqual(data[0]["viaf_id"], "http://www.viaf.org/viaf/123")
        self.assertEqual(data[0]["name"], "Test Name")


class WikipediaMixinTests(TestCase):
    def test_get_wikilinks_builds_urls(self):
        mixin = WikipediaMixin()
        with patch("authority.views.wikipedia_views.wikipedia.search", return_value=["Vladimir Lenin"]):
            data = mixin.get_wikilinks("Lenin", "en")

        self.assertEqual(data[0]["url"], "http://en.wikipedia.org/wiki/Vladimir Lenin")
