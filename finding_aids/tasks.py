# Create your tasks here
from celery import shared_task
from finding_aids.indexers.finding_aids_catalog_indexer import FindingAidsCatalogIndexer
from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer


@shared_task
def index_catalog_finding_aids_entity(finding_aids_entity_id):
    indexer = FindingAidsCatalogIndexer(finding_aids_entity_id)
    indexer.index()
    indexer_new = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer_new.index_with_requests()


@shared_task
def index_catalog_finding_aids_entity_remove(finding_aids_entity_id):
    indexer = FindingAidsCatalogIndexer(finding_aids_entity_id)
    indexer.delete()
    indexer_new = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer_new.delete()
