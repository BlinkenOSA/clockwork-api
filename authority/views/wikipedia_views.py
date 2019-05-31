import wikipedia
from rest_framework.filters import SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from authority.models import Country


class WikipediaMixin(object):
    def get_wikilinks(self, query, lang):
        data = []
        wikipedia.set_lang(lang)

        if len(query) > 0:
            ws = wikipedia.search(query, results=2)
            for entry in ws:
                wiki_url = 'http://%s.wikipedia.org/wiki/%s' % (lang, entry)
                data.append(wiki_url)
        return data


class WikipediaList(WikipediaMixin, APIView):
    queryset = Country.objects.all()
    filter_backends = (SearchFilter,)
    search_fields = ('query',)

    def get(self, request, *args, **kwargs):
        query = request.query_params.get('query', '')
        lang = request.query_params.get('lang', 'en')
        data = self.get_wikilinks(query, lang)
        return Response(data)