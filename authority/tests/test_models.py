from django.test import TestCase
from unittest.mock import patch

from authority.models import Country, Person


class PersonTest(TestCase):
    """ Test module for Person model """

    def setUp(self):
        Person.objects.create(
            first_name='Mikhail',
            last_name='Gorbachev',
            wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev'
        )

    def test_name(self):
        person = Person.objects.get(wiki_url='https://en.wikipedia.org/wiki/Mikhail_Gorbachev')
        self.assertEqual(person.__str__(), "Gorbachev, Mikhail")

    @patch("authority.models.get_wikidata_entity_payload")
    def test_save_populates_wikidata_cache_when_wikidata_id_is_set(self, mock_get_wikidata_entity_payload):
        payload = {
            "title": "Hungary",
            "description": "country in Central Europe",
            "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
            "properties": {
                "image": "https://img.test/hungary.jpg",
                "coordinates": {"lat": 47, "long": 19},
                "geoshape": {"type": "FeatureCollection", "features": []},
            },
        }
        mock_get_wikidata_entity_payload.return_value = payload

        country = Country.objects.create(
            alpha3="HUN",
            country="Hungary test",
            wikidata_id="Q1058",
        )

        country.refresh_from_db()
        self.assertEqual(
            country.wikidata_cache,
            {
                "title": "Hungary",
                "description": "country in Central Europe",
                "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
                "properties": {
                    "coordinates": {"lat": 47, "long": 19},
                    "geoshape": {"type": "FeatureCollection", "features": []},
                },
            },
        )
        self.assertIsNotNone(country.wikidata_cache_updated_at)

    @patch("authority.models.get_wikidata_entity_payload")
    def test_save_clears_wikidata_cache_when_wikidata_id_is_removed(self, mock_get_wikidata_entity_payload):
        payload = {
            "title": "Hungary",
            "description": "country in Central Europe",
            "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
            "properties": {
                "image": "https://img.test/hungary.jpg",
                "coordinates": {"lat": 47, "long": 19},
                "geoshape": {"type": "FeatureCollection", "features": []},
            },
        }
        mock_get_wikidata_entity_payload.return_value = payload

        country = Country.objects.create(
            alpha3="HUN",
            country="Hungary test",
            wikidata_id="Q28",
        )
        country.refresh_from_db()
        self.assertEqual(
            country.wikidata_cache,
            {
                "title": "Hungary",
                "description": "country in Central Europe",
                "wikipedia": "https://en.wikipedia.org/wiki/Hungary",
                "properties": {
                    "coordinates": {"lat": 47, "long": 19},
                    "geoshape": {"type": "FeatureCollection", "features": []},
                },
            },
        )

        country.wikidata_id = None
        country.save()
        country.refresh_from_db()

        self.assertIsNone(country.wikidata_cache)
        self.assertIsNone(country.wikidata_cache_updated_at)
