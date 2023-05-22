from django.core.management import BaseCommand

from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer
from isad.models import Isad


class Command(BaseCommand):
    def handle(self, *args, **options):
        for isad in Isad.objects.all():
            if isad.published:
                indexer = ISADNewCatalogIndexer(isad.id)
                indexer.index()
