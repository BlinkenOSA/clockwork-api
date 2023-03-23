from django.core.management import BaseCommand

from isad.indexers.isad_catalog_indexer import ISADCatalogIndexer
from isad.models import Isad


class Command(BaseCommand):
    def handle(self, *args, **options):
        for isad in Isad.objects.all():
            if isad.published:
                indexer = ISADCatalogIndexer(isad.id)
                indexer.index()
