import json
from typing import List, Dict, Any

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class VIAFMixin(object):
    """
    Mixin providing helper methods for querying the
    Virtual International Authority File (VIAF).

    VIAF aggregates authority records from multiple national libraries.
    This mixin supports searching for:
        - persons
        - corporations
        - countries
        - places

    Results are normalized into a minimal structure suitable for
    authority linking and UI selection workflows.
    """

    def get_results_from_viaf(self, query: str, request_type: str) -> List[Dict[str, str]]:
        """
        Queries the VIAF search API for authority records.

        Args:
            query:
                Search string provided by the user.

            request_type:
                Type of authority to search.
                Supported values:
                    - "person"
                    - "corporation"
                    - "country"
                    - "place"

        Returns:
            A list of dictionaries with keys:
                - viaf_id: URL of the VIAF authority record
                - name: Preferred heading
        """

        if not query:
            return []

        if request_type == 'person':
            query = 'local.names all "' + query + '"'
        elif request_type == 'corporation':
            query = 'local.corporateNames all "' + query + '"'
        elif request_type == 'country':
            query = 'local.geographicNames all "' + query + '"'
        elif request_type == 'place':
            query = 'local.geographicNames all "' + query + '"'

        session = requests.Session()
        session.trust_env = False

        r = session.get('http://www.viaf.org/viaf/search?query=%s&maximumRecords=5&sortKey=holdingscount' % query,
                        headers={'Accept': 'application/json'}, timeout=10)
        if r.status_code == 200:
            session.close()
            return self.assemble_data_stream(json.loads(r.text))
        else:
            session.close()
            return []

    @staticmethod
    def assemble_record(record: Dict[str, Any], counter: int) -> Dict[str, str]:
        """
        Extracts a single VIAF record from the API response.

        VIAF uses namespace-prefixed keys (e.g. ns2:, ns3:) which vary
        by record position. The counter is used to dynamically access
        these fields.

        Args:
            record:
                Raw VIAF record dictionary.

            counter:
                Namespace counter used in VIAF response keys.

        Returns:
            A dictionary containing:
                - viaf_id: VIAF authority URL
                - name: Preferred heading
        """

        record_data = record['recordData']
        viaf_id = 'http://www.viaf.org/viaf/%s' % record_data[f'ns{counter}:VIAFCluster'][f'ns{counter}:viafID']

        if isinstance(record_data[f'ns{counter}:VIAFCluster'][f'ns{counter}:mainHeadings'][f'ns{counter}:data'], list):
            name = record_data[f'ns{counter}:VIAFCluster'][f'ns{counter}:mainHeadings'][f'ns{counter}:data'][0][
                f'ns{counter}:text']
        else:
            name = record_data[f'ns{counter}:VIAFCluster'][f'ns{counter}:mainHeadings'][f'ns{counter}:data'][
                f'ns{counter}:text']

        rec = {
            'viaf_id': viaf_id,
            'name': name
        }
        return rec

    def assemble_data_stream(self, json_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extracts VIAF records from the search response.

        The VIAF API returns either:
            - a single record as a dictionary
            - multiple records as a list

        Namespace counters increment per record and must be tracked
        manually.

        Args:
            json_data:
                Parsed JSON response from VIAF.

        Returns:
            A list of normalized VIAF authority records.
        """

        data = []
        counter = 2
        if 'records' in json_data['searchRetrieveResponse']:
            if json_data['searchRetrieveResponse']['records']['record'].__class__.__name__ == 'dict':
                rec = self.assemble_record(json_data['searchRetrieveResponse']['records']['record'], counter)
                data.append(rec)
            else:
                for record in json_data['searchRetrieveResponse']['records']['record']:
                    rec = self.assemble_record(record, counter)
                    data.append(rec)
                    counter += 1
        return data


class VIAFList(VIAFMixin, APIView):
    """
    API endpoint for querying VIAF authority records.

    Query parameters:
        query:
            Search string.

        type:
            Authority type.
            Defaults to "person".

    Response:
        A JSON array of objects:
            {
                "viaf_id": "<VIAF authority URL>",
                "name": "<preferred heading>"
            }

    Typically used for authority enrichment and external linking.
    """

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests for VIAF authority lookup.

        Returns:
            HTTP 200 with a list of VIAF authority records.
        """

        query = request.query_params.get('query', '')
        type = request.query_params.get('type', 'person')
        data = self.get_results_from_viaf(query, type)
        return Response(data)