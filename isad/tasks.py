# Create your tasks here
from celery import shared_task

from isad.indexers.isad_catalog_indexer import ISADCatalogIndexer
from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer


@shared_task
def index_catalog_isad_record(isad_id):
    indexer = ISADCatalogIndexer(isad_id)
    indexer.index()
    indexer = ISADNewCatalogIndexer(isad_id)
    indexer.index_with_requests()


@shared_task
def index_catalog_isad_record_remove(isad_id):
    indexer = ISADCatalogIndexer(isad_id)
    indexer.delete()
    indexer = ISADNewCatalogIndexer(isad_id)
    indexer.delete()