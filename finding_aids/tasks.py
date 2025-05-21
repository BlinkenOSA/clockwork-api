# Create your tasks here
from celery import shared_task
from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer


@shared_task
def index_catalog_finding_aids_entity(finding_aids_entity_id):
    indexer = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer.index()
    indexer.commit()


@shared_task
def index_catalog_finding_aids_entity_remove(finding_aids_entity_id):
    indexer = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer.delete()

