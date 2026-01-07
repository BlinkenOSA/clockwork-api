import json
from typing import List, Dict, Any

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class WikidataMixin(object):
    """
    Mixin providing helper methods for querying the Wikidata search API.

    This mixin performs a full-text search against Wikidata entities and
    returns a normalized subset of the results suitable for authority
    linking and UI selection components.
    """

    def get_wikidata_links(self, query: str) -> List[Dict[str, str]]:
        """
        Queries Wikidata for entities matching the provided query string.

        Args:
            query:
                Search query string.

        Returns:
            A list of dictionaries with keys:
                - wikidata_id: Wikidata entity ID (e.g. "Q42")
                - wikidata_url: Full URL to the entity page
                - name: Display label including snippet context
        """

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
    def assemble_data_stream(json_data: Any) -> List[Dict[str, str]]:
        """
        Extracts and normalizes relevant data from a Wikidata API response.

        The Wikidata search API returns a structured JSON object containing
        search results with entity IDs, title snippets, and optional
        descriptive snippets.

        Args:
            json_data:
                Parsed JSON response from the Wikidata API.

        Returns:
            A list of dictionaries containing:
                - wikidata_id
                - wikidata_url
                - name (human-readable label with context)
        """

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
    """
    API endpoint for searching Wikidata entities.

    Query parameters:
        query:
            Search string.

    Response:
        A JSON array of objects:
            {
                "wikidata_id": "Q42",
                "wikidata_url": "https://www.wikidata.org/wiki/Q42",
                "name": "Douglas Adams (English writer)"
            }

    Typically used for authority linking or enrichment workflows.
    """

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        data = self.get_wikidata_links(query)
        return Response(data)