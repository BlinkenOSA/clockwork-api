from django.core.management import BaseCommand
from django.db.models.aggregates import Count

from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer
from finding_aids.models import FindingAidsEntity


class Command(BaseCommand):
    def handle(self, *args, **options):
        duplications = FindingAidsEntity.objects.values('catalog_id')\
            .annotate(count=Count('id'))\
            .order_by()\
            .filter(count__gt=1)

        for fa in FindingAidsEntity.objects.filter(catalog_id__in=[item['catalog_id'] for item in duplications]):
            indexer = FindingAidsNewCatalogIndexer(fa.id)
            indexer.delete()

            fa.set_catalog_id()
            fa.save()
            print("Saving %s with new catalog_id: %s" % (fa.archival_reference_code, fa.catalog_id))