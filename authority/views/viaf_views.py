import json

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class VIAFMixin(object):
    def get_results_from_viaf(self, query, request_type):
        if len(query) == 0:
            return []
        else:
            if request_type == 'person':
                query = 'local.personalNames+all+"' + query + '"'
            elif request_type == 'corporation':
                query = 'local.corporateNames+all+"' + query + '"'
            elif request_type == 'country':
                query = 'local.geographicNames+all+"' + query + '"'
            elif request_type == 'place':
                query = 'local.geographicNames+all+"' + query + '"'

            session = requests.Session()
            session.trust_env = False

            r = session.get('http://www.viaf.org/viaf/search?query=%s&sortKeys=holdingscount&maximumRecords=5&httpAccept'
                            '=application/json&recordSchema=http://viaf.org/BriefVIAFCluster' % query)
            if r.status_code == 200:
                return self.assemble_data_stream(json.loads(r.text))
            else:
                return []


    @staticmethod
    def assemble_data_stream(json_data):
        data = []
        counter = 1
        if 'records' in json_data['searchRetrieveResponse']:
            for record in json_data['searchRetrieveResponse']['records']:
                record_data = record['record']['recordData']
                viaf_id = 'http://www.viaf.org/viaf/%s' % record_data['viafID']['#text']

                if isinstance(record_data['mainHeadings']['data'], list):
                    name = record_data['mainHeadings']['data'][0]['text']
                else:
                    name = record_data['mainHeadings']['data']['text']

                rec = {
                    'viaf_id': viaf_id,
                    'name': name
                }
                data.append(rec)
                counter += 1
        return data


class VIAFList(VIAFMixin, APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        type = request.query_params.get('type', 'person')
        data = self.get_results_from_viaf(query, type)
        return Response(data)