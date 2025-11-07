import json

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class WikidataMixin(object):
    def get_wikidata_links(self, query):
        if len(query) == 0:
            return []
        else:
            session = requests.Session()
            session.trust_env = False

            r = session.get(
                'https://www.wikidata.org/w/api.php',
                headers={
                    'User-Agent': 'Blinken OSA Archivum - Archival Management System'
                },
                params={
                    'action': 'query',
                    'list': 'search',
                    'srprop': 'snippet|titlesnippet',
                    'srsearch': query,
                    'format': 'json'
                }
            )
            if r.status_code == 200:
                session.close()
                return self.assemble_data_stream(json.loads(r.text))
            else:
                session.close()
                return []

    @staticmethod
    def assemble_data_stream(json_data):
        data = []

        if json_data['query']['searchinfo']['totalhits'] > 0:
            for record in json_data['query']['search']:
                id = record['title']
                rec = {
                    'wikidata_id': id,
                    'wikidata_url': 'https://www.wikidata.org/wiki/%s' % id
                }
                if 'snippet' in record:
                    rec['name'] = "%s (%s)" % (record['titlesnippet'], record['snippet'])
                else:
                    rec['name'] = record['titlesnippet']
                data.append(rec)
        return data


class WikidataList(WikidataMixin, APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        data = self.get_wikidata_links(query)
        return Response(data)