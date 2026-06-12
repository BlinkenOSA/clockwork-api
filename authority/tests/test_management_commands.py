from io import StringIO
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase

from authority.models import Corporation, Country, Language, Person


class BackfillWikidataCacheCommandTests(TestCase):
    @patch("authority.management.commands.backfill_wikidata_cache.get_wikidata_entity_payload")
    def test_backfill_populates_missing_cache_only(self, mock_get_wikidata_entity_payload):
        mock_get_wikidata_entity_payload.return_value = {
            "title": "Hungary",
            "description": "country in Central Europe",
            "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
            "properties": {"image": "https://img.test/hungary.jpg"},
        }

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            missing_cache = Country.objects.create(alpha3="HUN", country="Hungary test", wikidata_id="Q28")
            cached = Language.objects.create(
                iso_639_3="eng",
                language="English test",
                wikidata_id="Q1860",
                wikidata_cache={"title": "English"},
            )

        out = StringIO()
        call_command("backfill_wikidata_cache", stdout=out)

        missing_cache.refresh_from_db()
        cached.refresh_from_db()

        self.assertEqual(missing_cache.wikidata_cache["title"], "Hungary")
        self.assertEqual(missing_cache.wikidata_cache["properties"], {})
        self.assertIsNotNone(missing_cache.wikidata_cache_updated_at)
        self.assertEqual(cached.wikidata_cache, {"title": "English"})
        mock_get_wikidata_entity_payload.assert_called_once_with("Q28")

    @patch("authority.management.commands.backfill_wikidata_cache.get_wikidata_entity_payload")
    def test_backfill_force_refreshes_existing_cache(self, mock_get_wikidata_entity_payload):
        mock_get_wikidata_entity_payload.return_value = {
            "title": "English refreshed",
            "description": "West Germanic language",
            "wikipedia": "https://en.wikipedia.org/wiki/English_language",
            "properties": {},
        }

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            language = Language.objects.create(
                iso_639_3="eng",
                language="English force test",
                wikidata_id="Q1860",
                wikidata_cache={"title": "Old English"},
            )

        call_command("backfill_wikidata_cache", "--force")

        language.refresh_from_db()
        self.assertEqual(language.wikidata_cache["title"], "English refreshed")
        mock_get_wikidata_entity_payload.assert_called_once_with("Q1860")


class BackfillCountryGeoshapesCommandTests(TestCase):
    @patch("authority.management.commands.backfill_country_geoshapes.get_wikidata_entity_payload")
    def test_backfill_updates_only_countries_missing_geoshape(self, mock_get_wikidata_entity_payload):
        mock_get_wikidata_entity_payload.return_value = {
            "title": "Algeria",
            "description": "country in North Africa",
            "wikipedia": "https://en.wikipedia.org/wiki/Algeria",
            "properties": {
                "image": "https://img.test/algeria.jpg",
                "coordinates": {"lat": 28, "long": 1},
                "geoshape": {"type": "FeatureCollection", "features": []},
            },
        }

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            missing_geoshape = Country.objects.create(
                alpha3="DZA",
                country="Algeria test",
                wikidata_id="Q262",
                wikidata_cache={
                    "title": "Algeria",
                    "properties": {"coordinates": {"lat": 28, "long": 1}},
                },
            )
            already_has_geoshape = Country.objects.create(
                alpha3="ALB",
                country="Albania test",
                wikidata_id="Q222",
                wikidata_cache={
                    "title": "Albania",
                    "properties": {"geoshape": {"type": "FeatureCollection", "features": []}},
                },
            )

        out = StringIO()
        call_command("backfill_country_geoshapes", stdout=out)

        missing_geoshape.refresh_from_db()
        already_has_geoshape.refresh_from_db()

        self.assertEqual(
            missing_geoshape.wikidata_cache["properties"],
            {
                "coordinates": {"lat": 28, "long": 1},
                "geoshape": {"type": "FeatureCollection", "features": []},
            },
        )
        self.assertEqual(
            already_has_geoshape.wikidata_cache,
            {
                "title": "Albania",
                "properties": {"geoshape": {"type": "FeatureCollection", "features": []}},
            },
        )
        mock_get_wikidata_entity_payload.assert_called_once_with("Q262")

    @patch("authority.management.commands.backfill_country_geoshapes.get_wikidata_entity_payload")
    def test_backfill_skips_payloads_still_missing_geoshape(self, mock_get_wikidata_entity_payload):
        mock_get_wikidata_entity_payload.return_value = {
            "title": "Algeria",
            "description": "country in North Africa",
            "wikipedia": "https://en.wikipedia.org/wiki/Algeria",
            "properties": {"coordinates": {"lat": 28, "long": 1}},
        }

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            country = Country.objects.create(
                alpha3="DZA",
                country="Algeria still missing geoshape",
                wikidata_id="Q262",
                wikidata_cache={
                    "title": "Algeria",
                    "properties": {"coordinates": {"lat": 28, "long": 1}},
                },
            )

        call_command("backfill_country_geoshapes")

        country.refresh_from_db()
        self.assertEqual(
            country.wikidata_cache,
            {
                "title": "Algeria",
                "properties": {"coordinates": {"lat": 28, "long": 1}},
            },
        )
        mock_get_wikidata_entity_payload.assert_called_once_with("Q262")


class BackfillPersonWikidataIdsCommandTests(TestCase):
    @patch("authority.management.commands.backfill_person_wikidata_ids.resolve_person_wikidata_id")
    def test_backfill_updates_missing_person_wikidata_id(self, mock_resolve_person_wikidata_id):
        mock_resolve_person_wikidata_id.return_value = (
            "Q42",
            {
                "status": "resolved",
                "source": "wikipedia",
                "wikipedia_id": "Q42",
                "viaf_id": None,
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None), patch(
            "authority.models.simhash64", return_value=1
        ):
            person = Person.objects.create(
                first_name="Douglas",
                last_name="Adams",
                wiki_url="https://en.wikipedia.org/wiki/Douglas_Adams",
            )

        out = StringIO()
        with patch("authority.models.simhash64", return_value=1):
            call_command("backfill_person_wikidata_ids", stdout=out)

        person.refresh_from_db()
        self.assertEqual(person.wikidata_id, "Q42")
        mock_resolve_person_wikidata_id.assert_called_once_with(
            wiki_url="https://en.wikipedia.org/wiki/Douglas_Adams",
            authority_url="",
        )

    @patch("authority.management.commands.backfill_person_wikidata_ids.resolve_person_wikidata_id")
    def test_backfill_skips_conflicts(self, mock_resolve_person_wikidata_id):
        mock_resolve_person_wikidata_id.return_value = (
            None,
            {
                "status": "conflict",
                "source": None,
                "wikipedia_id": "Q42",
                "viaf_id": "Q1",
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None), patch(
            "authority.models.simhash64", return_value=1
        ):
            person = Person.objects.create(
                first_name="Douglas",
                last_name="Adams",
                wiki_url="https://en.wikipedia.org/wiki/Douglas_Adams",
                authority_url="http://www.viaf.org/viaf/113230702",
            )

        call_command("backfill_person_wikidata_ids")

        person.refresh_from_db()
        self.assertIsNone(person.wikidata_id)

    @patch("authority.management.commands.backfill_person_wikidata_ids.resolve_person_wikidata_id")
    def test_backfill_dry_run_does_not_save(self, mock_resolve_person_wikidata_id):
        mock_resolve_person_wikidata_id.return_value = (
            "Q42",
            {
                "status": "resolved",
                "source": "viaf",
                "wikipedia_id": None,
                "viaf_id": "Q42",
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None), patch(
            "authority.models.simhash64", return_value=1
        ):
            person = Person.objects.create(
                first_name="Douglas",
                last_name="Adams",
                authority_url="http://www.viaf.org/viaf/113230702",
            )

        call_command("backfill_person_wikidata_ids", "--dry-run")

        person.refresh_from_db()
        self.assertIsNone(person.wikidata_id)


class BackfillCorporationWikidataIdsCommandTests(TestCase):
    @patch("authority.management.commands.backfill_corporation_wikidata_ids.resolve_corporation_wikidata_id")
    def test_backfill_updates_missing_corporation_wikidata_id(self, mock_resolve_corporation_wikidata_id):
        mock_resolve_corporation_wikidata_id.return_value = (
            "Q95",
            {
                "status": "resolved",
                "source": "wikipedia",
                "wikipedia_id": "Q95",
                "viaf_id": None,
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            corporation = Corporation.objects.create(
                name="Google",
                wiki_url="https://en.wikipedia.org/wiki/Google",
            )

        out = StringIO()
        call_command("backfill_corporation_wikidata_ids", stdout=out)

        corporation.refresh_from_db()
        self.assertEqual(corporation.wikidata_id, "Q95")
        mock_resolve_corporation_wikidata_id.assert_called_once_with(
            wiki_url="https://en.wikipedia.org/wiki/Google",
            authority_url="",
        )

    @patch("authority.management.commands.backfill_corporation_wikidata_ids.resolve_corporation_wikidata_id")
    def test_backfill_skips_corporation_conflicts(self, mock_resolve_corporation_wikidata_id):
        mock_resolve_corporation_wikidata_id.return_value = (
            None,
            {
                "status": "conflict",
                "source": None,
                "wikipedia_id": "Q95",
                "viaf_id": "Q1",
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            corporation = Corporation.objects.create(
                name="Google",
                wiki_url="https://en.wikipedia.org/wiki/Google",
                authority_url="http://www.viaf.org/viaf/136145864",
            )

        call_command("backfill_corporation_wikidata_ids")

        corporation.refresh_from_db()
        self.assertIsNone(corporation.wikidata_id)

    @patch("authority.management.commands.backfill_corporation_wikidata_ids.resolve_corporation_wikidata_id")
    def test_backfill_corporation_dry_run_does_not_save(self, mock_resolve_corporation_wikidata_id):
        mock_resolve_corporation_wikidata_id.return_value = (
            "Q95",
            {
                "status": "resolved",
                "source": "viaf",
                "wikipedia_id": None,
                "viaf_id": "Q95",
            },
        )

        with patch("authority.models.get_wikidata_entity_payload", return_value=None):
            corporation = Corporation.objects.create(
                name="Google",
                authority_url="http://www.viaf.org/viaf/136145864",
            )

        call_command("backfill_corporation_wikidata_ids", "--dry-run")

        corporation.refresh_from_db()
        self.assertIsNone(corporation.wikidata_id)
