import json

from django.core.management import BaseCommand
import requests

from authority.models import Country


class Command(BaseCommand):
    def handle(self, *args, **options):
        for country in Country.objects.all():
            if not country.wikidata_id:
                session = requests.Session()
                session.trust_env = False

                r = session.get(
                    'https://www.wikidata.org/w/api.php',
                    params={
                        'action': 'query',
                        'list': 'search',
                        'srprop': 'snippet|titlesnippet',
                        'srsearch': country.country,
                        'format': 'json'
                    }
                )
                if r.status_code == 200:
                    session.close()
                    json_data = json.loads(r.text)
                    if json_data['query']['searchinfo']['totalhits'] > 0:
                        data = json_data['query']['search'][0]
                        country.wikidata_id = data['title']
                        country.save()
                        print("Country %s was updated with the wikidata id: %s" % (country, data['title']))
