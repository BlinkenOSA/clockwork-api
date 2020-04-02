import json

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class LCSHMixin(object):
    def get_lcshlinks(self, query, request_type):
        if request_type == 'genre':
            rt = 'http://id.loc.gov/authorities/genreForms'
        elif request_type == 'subject':
            rt = 'http://id.loc.gov/authorities/subjects'

        if len(query) == 0 or len(request_type) == 0:
            return []
        else:
            session = requests.Session()
            session.trust_env = False

            r = session.get('http://id.loc.gov/search/?q=%s&q=cs:%s&format=json'
                            % (query, rt))
            if r.status_code == 200:
                return self.assemble_data_stream(json.loads(r.text))
            else:
                return []

    @staticmethod
    def assemble_data_stream(json_data):
        data = []
        counter = 1

        for record in json_data:
            if isinstance(record, list):
                if record[0] == 'atom:entry':
                    lcsh_id = record[3][1]['href']
                    rec = {
                        'lcsh_id': lcsh_id,
                        'name': record[2][2],
                    }
                    data.append(rec)
                    counter += 1
        return data


class LCSHList(LCSHMixin, APIView):
    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        type = request.query_params.get('type', 'genre')
        data = self.get_lcshlinks(query, type)
        return Response(data)