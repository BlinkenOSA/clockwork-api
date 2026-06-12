from unittest import TestCase
from unittest.mock import Mock, patch

from authority.services.wikidata_id_lookup import (
    resolve_authority_wikidata_id,
    resolve_corporation_wikidata_id,
    resolve_person_wikidata_id,
    resolve_wikidata_id_from_viaf_url,
    resolve_wikidata_id_from_wikipedia_url,
)


class WikidataIdLookupTests(TestCase):
    @patch("authority.services.wikidata_id_lookup.get")
    def test_resolve_wikidata_id_from_wikipedia_url(self, mock_get):
        response = Mock(status_code=200)
        response.json.return_value = {
            "query": {
                "pages": {
                    "123": {
                        "pageprops": {
                            "wikibase_item": "Q42",
                        }
                    }
                }
            }
        }
        mock_get.return_value = response

        wikidata_id = resolve_wikidata_id_from_wikipedia_url(
            "https://en.wikipedia.org/wiki/Douglas_Adams"
        )

        self.assertEqual(wikidata_id, "Q42")

    @patch("authority.services.wikidata_id_lookup.get")
    def test_resolve_wikidata_id_from_viaf_url(self, mock_get):
        response = Mock(status_code=200)
        response.json.return_value = {
            "search": [
                {
                    "id": "Q42",
                    "concepturi": "http://www.wikidata.org/entity/Q42",
                }
            ]
        }
        mock_get.return_value = response

        wikidata_id = resolve_wikidata_id_from_viaf_url(
            "http://www.viaf.org/viaf/113230702"
        )

        self.assertEqual(wikidata_id, "Q42")

    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_viaf_url")
    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_wikipedia_url")
    def test_resolve_person_wikidata_id_returns_conflict_when_sources_disagree(
        self,
        mock_resolve_wikipedia,
        mock_resolve_viaf,
    ):
        mock_resolve_wikipedia.return_value = "Q42"
        mock_resolve_viaf.return_value = "Q1"

        wikidata_id, meta = resolve_person_wikidata_id(
            wiki_url="https://en.wikipedia.org/wiki/Douglas_Adams",
            authority_url="http://www.viaf.org/viaf/113230702",
        )

        self.assertIsNone(wikidata_id)
        self.assertEqual(meta["status"], "conflict")

    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_viaf_url")
    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_wikipedia_url")
    def test_resolve_person_wikidata_id_prefers_agreeing_sources(
        self,
        mock_resolve_wikipedia,
        mock_resolve_viaf,
    ):
        mock_resolve_wikipedia.return_value = "Q42"
        mock_resolve_viaf.return_value = "Q42"

        wikidata_id, meta = resolve_person_wikidata_id(
            wiki_url="https://en.wikipedia.org/wiki/Douglas_Adams",
            authority_url="http://www.viaf.org/viaf/113230702",
        )

        self.assertEqual(wikidata_id, "Q42")
        self.assertEqual(meta["source"], "wikipedia+viaf")

    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_viaf_url")
    @patch("authority.services.wikidata_id_lookup.resolve_wikidata_id_from_wikipedia_url")
    def test_resolve_authority_wikidata_id_returns_single_source_match(
        self,
        mock_resolve_wikipedia,
        mock_resolve_viaf,
    ):
        mock_resolve_wikipedia.return_value = None
        mock_resolve_viaf.return_value = "Q95"

        wikidata_id, meta = resolve_authority_wikidata_id(
            wiki_url="",
            authority_url="http://www.viaf.org/viaf/136145864",
        )

        self.assertEqual(wikidata_id, "Q95")
        self.assertEqual(meta["source"], "viaf")

    @patch("authority.services.wikidata_id_lookup.resolve_authority_wikidata_id")
    def test_resolve_corporation_wikidata_id_delegates_to_shared_resolver(self, mock_resolve_authority):
        mock_resolve_authority.return_value = ("Q95", {"status": "resolved", "source": "wikipedia"})

        wikidata_id, meta = resolve_corporation_wikidata_id(
            wiki_url="https://en.wikipedia.org/wiki/Google",
            authority_url="http://www.viaf.org/viaf/136145864",
        )

        self.assertEqual(wikidata_id, "Q95")
        self.assertEqual(meta["source"], "wikipedia")
        mock_resolve_authority.assert_called_once_with(
            wiki_url="https://en.wikipedia.org/wiki/Google",
            authority_url="http://www.viaf.org/viaf/136145864",
        )
