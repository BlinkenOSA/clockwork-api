from django.core.management import BaseCommand

from isad.indexers.isad_meilisearch_indexer import ISADMeilisearchIndexer
from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer
from isad.models import Isad


class Command(BaseCommand):
    def handle(self, *args, **options):
        for isad in Isad.objects.all():
            indexer = ISADMeilisearchIndexer(isad.id)
            if isad.published:
                print("Indexing %s" % indexer.isad.reference_code)
                indexer.index()
            else:
                indexer.delete()
