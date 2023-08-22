import json

import requests
from rest_framework.response import Response
from rest_framework.status import HTTP_404_NOT_FOUND
from rest_framework.views import APIView
from wikidata.client import Client
from pyWikiCommons import pyWikiCommons

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
    permission_classes = []

    def get(self, request, wikidata_id, *args, **kwargs):
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
                                r = requests.get(commons_api, params=params)
                                if r.status_code == 200:
                                    j = r.json()
                                    first_key = list(j['query']['pages'].keys())[0]
                                    keys_dict[ACCEPTED_KEYS[ak]] = j['query']['pages'][first_key]['imageinfo'][0]['url']

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

                        elif ak == 'P106' or ak == 'P800':
                            if ACCEPTED_KEYS[ak] not in keys_dict.keys():
                                keys_dict[ACCEPTED_KEYS[ak]] = []
                            data_id = v['mainsnak']['datavalue']['value']['id']
                            property_entity = client.get(data_id, load=True)
                            keys_dict[ACCEPTED_KEYS[ak]].append(property_entity.label['en'])

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
                            r = requests.get(commons_api, params=params)
                            if r.status_code == 200:
                                j = r.json()
                                first_key = list(j['query']['pages'].keys())[0]
                                keys_dict['geojson'] = json.loads(j['query']['pages'][first_key]['revisions'][0]['*'])

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
        if 'en' in description.keys():
            return description['en']
        else:
            return description[list(description.keys())[0]]
