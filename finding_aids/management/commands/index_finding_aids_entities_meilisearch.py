import time

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
from finding_aids.indexers.finding_aids_meilisearch_indexer import FindingMeilisearchIndexer
from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--fonds', dest='fonds', help='Fonds Number')
        parser.add_argument('--subfonds', dest='subfonds', help='Subfonds Number')
        parser.add_argument('--series', dest='series', help='Series Number')
        parser.add_argument('--all', dest='all', help='Index everything.')

    def handle(self, *args, **options):
        if options['all']:
            for archival_unit in ArchivalUnit.objects.all():
                for fa in FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False).iterator():
                    indexer = FindingMeilisearchIndexer(fa.id)
                    if fa.published:
                        print("Indexing: %s" % fa.archival_reference_code)
                        indexer.index()
                        pass
                    else:
                        indexer.delete()
                time.sleep(2)

        else:
            archival_unit = ArchivalUnit.objects.get(fonds=options['fonds'],
                                                     subfonds=options['subfonds'],
                                                     series=options['series'])
            finding_aids_entities = FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False)
            for fa in finding_aids_entities.iterator():
                indexer = FindingMeilisearchIndexer(fa.id)
                if fa.published:
                    print("Indexing: %s" % fa.archival_reference_code)
                    indexer.index()
                else:
                    indexer.delete()
