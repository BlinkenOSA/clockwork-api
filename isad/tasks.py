# Create your tasks here
from celery import shared_task

from isad.indexers.isad_catalog_indexer import ISADCatalogIndexer


@shared_task
def index_catalog_isad_record(isad_id):
    indexer = ISADCatalogIndexer(isad_id)
    indexer.index()


@shared_task
def index_catalog_isad_record_remove(isad_id):
    indexer = ISADCatalogIndexer(isad_id)
    indexer.delete()
