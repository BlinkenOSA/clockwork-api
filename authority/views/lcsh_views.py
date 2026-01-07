import json
from typing import List, Dict, Any

import requests
from rest_framework.response import Response
from rest_framework.views import APIView


class LCSHMixin(object):
    """
    Mixin providing helper methods for querying the
    Library of Congress Subject Headings (LCSH) API.

    This mixin supports querying:
        - LCSH Subject Headings
        - LCSH Genre/Form Terms

    The returned data is normalized into a lightweight structure
    suitable for frontend autocomplete or selection components.
    """

    def get_lcshlinks(self, query: str, request_type: str) -> List[Dict[str, str]]:
        """
        Queries the Library of Congress API for subject or genre terms.

        Args:
            query:
                Search query string provided by the user.

            request_type:
                Type of LCSH authority to query.
                Supported values:
                    - "genre"
                    - "subject"

        Returns:
            A list of dictionaries with keys:
                - lcsh_id: URL of the LCSH authority record
                - name: Human-readable label
        """

        if request_type == 'genre':
            rt = 'http://id.loc.gov/authorities/genreForms'
        elif request_type == 'subject':
            rt = 'http://id.loc.gov/authorities/subjects'

        if len(query) == 0 or len(request_type) == 0:
            return []
        else:
            session = requests.Session()
            session.trust_env = False

            r = session.get('http://id.loc.gov/search/?q=%s&q=cs:%s&format=json' % (query, rt))
            if r.status_code == 200:
                session.close()
                return self.assemble_data_stream(json.loads(r.text))
            else:
                session.close()
                return []

    @staticmethod
    def assemble_data_stream(json_data: Any) -> List[Dict[str, str]]:
        """
        Extracts relevant authority data from the LoC JSON response.

        The LoC API returns a loosely structured JSON array where
        authority records are embedded in list entries labeled
        as 'atom:entry'.

        Args:
            json_data:
                Parsed JSON response from the LoC API.

        Returns:
            A list of dictionaries with keys:
                - lcsh_id: Authority record URL
                - name: Preferred label
        """

        data = []

        for record in json_data:
            if isinstance(record, list):
                if record[0] == 'atom:entry':
                    lcsh_id = record[3][1]['href']
                    rec = {
                        'lcsh_id': lcsh_id,
                        'name': record[2][2],
                    }
                    data.append(rec)
        return data


class LCSHList(LCSHMixin, APIView):
    """
    API endpoint for searching Library of Congress Subject Headings.

    Query parameters:
        query:
            Search string.

        type:
            Authority type to query.
            Allowed values:
                - "genre" (default)
                - "subject"

    Response:
        A JSON array of objects:
            {
                "lcsh_id": "<authority URL>",
                "name": "<preferred label>"
            }

    This endpoint is typically used by autocomplete widgets or
    authority lookup dialogs.
    """

    def get(self, request, *args, **kwargs) -> Response:
        """
        Handles GET requests for LCSH lookup.

        Returns:
            HTTP 200 with a list of LCSH authority records.
        """

        query = request.query_params.get('query', '')
        type = request.query_params.get('type', 'genre')
        data = self.get_lcshlinks(query, type)
        return Response(data)