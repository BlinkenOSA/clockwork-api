import json
import logging
import time

from clockwork_api.http import get
from requests.exceptions import RequestException
from wikidata.client import Client

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

WIKIMEDIA_HEADERS = {
    'User-Agent': 'Blinken OSA Archivum - Archival Management System'
}

COMMONS_API_URL = 'https://commons.wikimedia.org/w/api.php'
COMMONS_RETRY_STATUS_CODES = {429, 503}
COMMONS_RETRY_DELAYS = (1.0, 2.0, 5.0)

logger = logging.getLogger(__name__)


def _should_retry_commons_response(response):
    if response.status_code in COMMONS_RETRY_STATUS_CODES:
        return True

    try:
        body = response.text.lower()
    except Exception:
        body = ''

    return 'maxlag' in body


def _get_commons_response(params):
    last_response = None

    for attempt, delay in enumerate((0,) + COMMONS_RETRY_DELAYS):
        if delay:
            time.sleep(delay)

        try:
            response = get(COMMONS_API_URL, headers=WIKIMEDIA_HEADERS, params=params)
        except RequestException as exc:
            logger.warning("Commons API request failed on attempt %s: %s", attempt + 1, exc)
            last_response = None
            if attempt == len(COMMONS_RETRY_DELAYS):
                return None
            continue

        if response.status_code == 200:
            return response

        last_response = response
        if attempt == len(COMMONS_RETRY_DELAYS) or not _should_retry_commons_response(response):
            logger.warning(
                "Commons API request returned %s for params %s",
                response.status_code,
                params,
            )
            return response

        logger.warning(
            "Commons API request returned %s on attempt %s, retrying",
            response.status_code,
            attempt + 1,
        )

    return last_response


def _get_commons_map_geojson(data_id):
    params = {
        'action': 'query',
        'titles': data_id,
        'prop': 'revisions',
        'rvprop': 'content',
        'rvslots': 'main',
        'format': 'json'
    }
    response = _get_commons_response(params)

    if not response or response.status_code != 200:
        return None

    data = response.json()
    pages = data.get('query', {}).get('pages', {})
    first_key = next(iter(pages), None)
    revisions = pages.get(first_key, {}).get('revisions', []) if first_key else []
    if not revisions:
        return None

    revision = revisions[0]
    revision_content = revision.get('*')
    if revision_content is None:
        revision_content = revision.get('slots', {}).get('main', {}).get('*')

    if revision_content is None:
        return None

    try:
        return json.loads(revision_content)
    except json.JSONDecodeError:
        return None


def get_wikidata_entity_payload(wikidata_id: str):
    """
    Builds the curated Wikidata payload used by the public catalog.

    Returns None when the entity cannot be loaded.
    """

    client = Client()
    entity = client.get(wikidata_id, load=True)
    if not getattr(entity, 'data', None):
        return None

    keys_dict = {}
    claims = entity.data.get('claims', {})

    for accepted_key, output_key in ACCEPTED_KEYS.items():
        if accepted_key not in claims:
            continue

        for value in claims[accepted_key]:
            if accepted_key == 'P17':
                if len(claims[accepted_key]) > 1 and value.get('rank') != 'preferred':
                    break
                data_id = value['mainsnak']['datavalue']['value']['id']
                property_entity = client.get(data_id, load=True)
                keys_dict[output_key] = property_entity.label['en']

            elif accepted_key == 'P18':
                if 'datavalue' not in value['mainsnak']:
                    continue

                data_url = value['mainsnak']['datavalue']['value'].replace(' ', '_')
                params = {
                    'action': 'query',
                    'titles': 'File:%s' % data_url,
                    'prop': 'imageinfo',
                    'iiprop': 'url',
                    'format': 'json'
                }
                response = _get_commons_response(params)

                if response and response.status_code == 200:
                    data = response.json()
                    pages = data.get('query', {}).get('pages', {})
                    first_key = next(iter(pages), None)
                    imageinfo = pages.get(first_key, {}).get('imageinfo', []) if first_key else []
                    if imageinfo:
                        keys_dict[output_key] = imageinfo[0].get('url')

            elif accepted_key == 'P625':
                keys_dict[output_key] = {
                    'lat': value['mainsnak']['datavalue']['value']['latitude'],
                    'long': value['mainsnak']['datavalue']['value']['longitude']
                }

            elif accepted_key in ('P569', 'P570'):
                keys_dict[output_key] = value['mainsnak']['datavalue']['value']['time']

            elif accepted_key in ('P106', 'P800'):
                if output_key not in keys_dict:
                    keys_dict[output_key] = []
                data_id = value['mainsnak']['datavalue']['value']['id']
                property_entity = client.get(data_id, load=True)
                keys_dict[output_key].append(property_entity.label['en'])

            elif accepted_key == 'P3896':
                data_id = value['mainsnak']['datavalue']['value']
                geojson = _get_commons_map_geojson(data_id)
                if geojson is not None:
                    keys_dict[output_key] = geojson

            else:
                data_id = value['mainsnak']['datavalue']['value']['id']
                property_entity = client.get(data_id, load=True)
                keys_dict[output_key] = property_entity.label['en']

    wikipedia = ''
    sitelinks = entity.data.get('sitelinks', {})
    for wikikey in WIKIPEDIA_LINKS:
        if wikikey in sitelinks:
            wikipedia = sitelinks[wikikey]['url']
            break

    return {
        'title': entity.label['en'],
        'description': get_best_description(entity.description),
        'wikipedia': wikipedia,
        'properties': keys_dict
    }


def get_best_description(description):
    if 'en' in description.keys():
        return description['en']
    return description[list(description.keys())[0]]
