from typing import List, Dict

import wikipedia
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from authority.models import Country


class WikipediaMixin(object):
    """
    Mixin providing helper methods for querying Wikipedia.

    This mixin performs lightweight Wikipedia searches in a given
    language and returns direct article URLs suitable for authority
    enrichment and external linking.

    It intentionally limits results to a small number to avoid
    excessive API calls and ambiguous matches.
    """

    def get_wikilinks(self, query: str, lang: str) -> List[Dict[str, str]]:
        """
        Searches Wikipedia for a query string in a specific language.

        Args:
            query:
                Search string.

            lang:
                Wikipedia language code (e.g. "en", "ru", "hu").

        Returns:
            A list of dictionaries with keys:
                - name: Wikipedia page title
                - url: Full URL to the Wikipedia article
        """

        data = []

        if len(query) > 0:
            wikipedia.set_lang(lang)
            ws = wikipedia.search(query, results=2)
            for entry in ws:
                wiki_url = 'http://%s.wikipedia.org/wiki/%s' % (lang, entry)
                data.append({
                    'name': entry,
                    'url': wiki_url
                })
        return data


class WikipediaList(WikipediaMixin, APIView):
    """
    API endpoint for searching Wikipedia articles across multiple languages.

    Query parameters:
        query:
            Search string.

    Languages searched:
        - English (en)
        - Russian (ru)
        - Hungarian (hu)
        - German (de)
        - Polish (pl)
        - Italian (it)
        - Spanish (es)
        - French (fr)
        - Romanian (ro)
        - Czech (cs)
        - Bulgarian (bg)
        - Ukrainian (uk)

    Response:
        A JSON array of objects:
            {
                "name": "<article title>",
                "url": "<Wikipedia article URL>"
            }

    This endpoint is typically used for quick external reference
    suggestions rather than authoritative linking.
    """

    queryset = Country.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ('query',)

    def get(self, request, *args, **kwargs) -> Response:
        """
        Handles GET requests for Wikipedia article lookup.

        Returns:
            HTTP 200 with a combined list of Wikipedia search results
            from multiple languages.
        """

        data = []
        languages = ['en', 'ru', 'hu', 'de', 'pl', 'it', 'es', 'fr', 'ro', 'cs', 'bg', 'uk']

        query = request.query_params.get('query', '')

        if query != '':
            for lang in languages:
                data += self.get_wikilinks(query, lang)
        return Response(data)