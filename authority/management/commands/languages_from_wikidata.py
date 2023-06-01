import json

from django.core.management import BaseCommand
import requests

from authority.models import Country, Language


class Command(BaseCommand):
    def handle(self, *args, **options):
        for language in Language.objects.all():
            if not language.wikidata_id:
                session = requests.Session()
                session.trust_env = False

                r = session.get(
                    'https://www.wikidata.org/w/api.php',
                    params={
                        'action': 'query',
                        'list': 'search',
                        'srprop': 'snippet|titlesnippet',
                        'srsearch': language.language,
                        'format': 'json'
                    }
                )
                if r.status_code == 200:
                    session.close()
                    json_data = json.loads(r.text)
                    if json_data['query']['searchinfo']['totalhits'] > 0:
                        data = json_data['query']['search'][0]
                        language.wikidata_id = data['title']
                        language.save()
                        print("Language %s was updated with the wikidata id: %s" % (language, data['title']))
