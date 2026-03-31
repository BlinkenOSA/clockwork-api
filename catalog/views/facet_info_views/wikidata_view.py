"""
Wikidata facet enrichment view for the public catalog.

This module provides a read-only endpoint that fetches and normalizes
selected Wikidata properties for display in catalog facet panels.

The view intentionally:
    - restricts exposed properties to a curated whitelist
    - resolves human-readable labels eagerly
    - aggregates data from Wikidata and Wikimedia Commons
    - avoids exposing raw Wikidata structures to the frontend

This endpoint is used for contextual enrichment, not authority control.
"""

import json

from clockwork_api.http import get
from requests.exceptions import RequestException
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from wikidata.client import Client
from pyWikiCommons import pyWikiCommons

# ---------------------------------------------------------------------
# Wikidata configuration
# ---------------------------------------------------------------------

ACCEPTED_KEYS = {
    'P17': 'country',
    'P18': 'image',
    'P19': 'place_of_birth',
    'P20': 'place_of_death',
    'P106': 'occupation',
    'P569': 'date_of_birth',
    'P570': 'date_of_death',
    'P625': 'coordinates',
    'P800': 'notable_work',
    'P3896': 'geoshape'
}

WIKIPEDIA_LINKS = [
    'enwiki', 'huwiki', 'ruwiki', 'plwiki', 'dewiki'
]


class WikidataView(APIView):
    """
    Returns curated Wikidata information for a given Wikidata entity.

    This view is used when a user clicks on a facet that is linked to
    a Wikidata identifier. It retrieves the entity, extracts a limited
    set of approved properties, resolves them to human-readable values,
    and returns a frontend-friendly structure.

    Design decisions:
        - Only a curated subset of Wikidata properties is exposed
        - All labels are resolved in English
        - Wikimedia Commons is queried for images and geoshapes
        - Raw Wikidata claims are never returned directly

    This endpoint is intentionally read-only and public.
    """

    permission_classes = []

    def get(self, request, wikidata_id: str, *args, **kwargs) -> Response:
        """
        Retrieves Wikidata enrichment data for a single entity.

        Args:
            wikidata_id:
                Wikidata entity identifier (e.g. "Q42").

        Returns:
            JSON response containing:
                - title: English label of the entity
                - description: Best available description text
                - wikipedia: URL of the first available Wikipedia article
                - properties: Dictionary of curated, normalized properties

        Returns HTTP 404 if the entity cannot be loaded.
        """

        client = Client()
        entity = client.get(wikidata_id, load=True)
        if entity.data:
            keys_dict = {}
            keys = entity.data['claims'].keys()

            for ak in ACCEPTED_KEYS.keys():
                if ak in keys:
                    for v in entity.data['claims'][ak]:

                        # Country
                        if ak == 'P17':
                            if len(entity.data['claims'][ak]) > 1:
                                if v['rank'] != 'preferred':
                                    break
                            data_id = v['mainsnak']['datavalue']['value']['id']
                            property_entity = client.get(data_id, load=True)
                            keys_dict[ACCEPTED_KEYS[ak]] = property_entity.label['en']

                        # Image
                        if ak == 'P18':
                            if 'datavalue' in v['mainsnak']:
                                data_url = v['mainsnak']['datavalue']['value'].replace(' ', '_')
                                commons_api = 'https://commons.wikimedia.org/w/api.php'
                                params = {
                                    'action': 'query',
                                    'titles': 'File:%s' % data_url,
                                    'prop': 'imageinfo',
                                    'iiprop': 'url',
                                    'format': 'json'
                                }
                                try:
                                    r = get(commons_api, params=params)
                                except RequestException:
                                    r = None

                                if r and r.status_code == 200:
                                    j = r.json()
                                    pages = j.get('query', {}).get('pages', {})
                                    first_key = next(iter(pages), None)
                                    imageinfo = pages.get(first_key, {}).get('imageinfo', []) if first_key else []
                                    if imageinfo:
                                        keys_dict[ACCEPTED_KEYS[ak]] = imageinfo[0].get('url')

                        # Coordinates
                        elif ak == 'P625':
                            data = {
                                'lat': v['mainsnak']['datavalue']['value']['latitude'],
                                'long': v['mainsnak']['datavalue']['value']['longitude']
                            }
                            keys_dict[ACCEPTED_KEYS[ak]] = data

                        # Dates of birth / death
                        elif ak == 'P569' or ak == 'P570':
                            data = v['mainsnak']['datavalue']['value']['time']
                            keys_dict[ACCEPTED_KEYS[ak]] = data

                        # Occupation / Notable work
                        elif ak == 'P106' or ak == 'P800':
                            if ACCEPTED_KEYS[ak] not in keys_dict.keys():
                                keys_dict[ACCEPTED_KEYS[ak]] = []
                            data_id = v['mainsnak']['datavalue']['value']['id']
                            property_entity = client.get(data_id, load=True)
                            keys_dict[ACCEPTED_KEYS[ak]].append(property_entity.label['en'])

                        # Geoshape
                        elif ak == 'P3896':
                            data_id = v['mainsnak']['datavalue']['value']
                            keys_dict[ACCEPTED_KEYS[ak]] = 'https://commons.wikimedia.org/wiki/%s' % data_id

                            commons_api = 'https://commons.wikimedia.org/w/api.php'
                            params = {
                                'action': 'query',
                                'titles': data_id,
                                'prop': 'revisions',
                                'rvprop': 'content',
                                'format': 'json'
                            }
                            try:
                                r = get(commons_api, params=params)
                            except RequestException:
                                r = None

                            if r and r.status_code == 200:
                                j = r.json()
                                pages = j.get('query', {}).get('pages', {})
                                first_key = next(iter(pages), None)
                                revisions = pages.get(first_key, {}).get('revisions', []) if first_key else []
                                if revisions and '*' in revisions[0]:
                                    keys_dict['geojson'] = json.loads(revisions[0]['*'])

                        else:
                            data_id = v['mainsnak']['datavalue']['value']['id']
                            property_entity = client.get(data_id, load=True)
                            keys_dict[ACCEPTED_KEYS[ak]] = property_entity.label['en']

                # Get Wikidata link
                wikipedia = ''
                for wikikey in WIKIPEDIA_LINKS:
                    if wikikey in entity.data['sitelinks'].keys():
                        wikipedia = entity.data['sitelinks'][wikikey]['url']
                        break

            return Response(
                {
                    'title': entity.label['en'],
                    'description': self._get_description(entity.description),
                    'wikipedia': wikipedia,
                    'properties': keys_dict
                }
            )

        else:
            return Response(status=HTTP_404_NOT_FOUND)

    def _get_description(self, description):
        """
        Returns the best available description for a Wikidata entity.

        Prefers English descriptions, but falls back to the first
        available language if English is not present.
        """

        if 'en' in description.keys():
            return description['en']
        else:
            return description[list(description.keys())[0]]
