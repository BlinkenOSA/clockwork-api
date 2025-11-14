import wikipedia
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from authority.models import Country


class WikipediaMixin(object):
    def get_wikilinks(self, query, lang):
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
    queryset = Country.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ('query',)

    def get(self, request, *args, **kwargs):
        data = []
        languages = ['en', 'ru', 'hu', 'de', 'pl', 'it', 'es', 'fr', 'ro', 'cs', 'bg', 'uk']

        query = request.query_params.get('query', '')

        if query != '':
            for lang in languages:
                data += self.get_wikilinks(query, lang)
        return Response(data)