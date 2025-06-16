import time

from django.core.management import BaseCommand

from archival_unit.models import ArchivalUnit
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
            archival_units = ArchivalUnit.objects.filter()
            counter = 0
            for archival_unit in archival_units.iterator():
                for fa in FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False).iterator():
                    indexer = FindingAidsNewCatalogIndexer(fa.id)
                    if fa.published:
                        indexer.index_with_requests()

                        if counter % 500 == 0:
                            print("Commit changes")
                            indexer = FindingAidsNewCatalogIndexer(1)
                            indexer.commit()
                            time.sleep(3)

                        counter += 1
                    else:
                        indexer.delete()

        else:
            archival_unit = ArchivalUnit.objects.get(fonds=options['fonds'],
                                                     subfonds=options['subfonds'],
                                                     series=options['series'])
            counter = 0
            finding_aids_entities = FindingAidsEntity.objects.filter(archival_unit=archival_unit, is_template=False)
            for fa in finding_aids_entities.iterator():
                indexer = FindingAidsNewCatalogIndexer(fa.id)
                if fa.published:
                    indexer.index_with_requests()

                    if counter % 500 == 0:
                        print("Commit changes")
                        indexer = FindingAidsNewCatalogIndexer(1)
                        indexer.commit()
                        time.sleep(3)

                    counter += 1
                else:
                    indexer.delete()

        indexer = FindingAidsNewCatalogIndexer(1)
        indexer.commit()