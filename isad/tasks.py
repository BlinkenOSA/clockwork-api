# Create your tasks here
from celery import shared_task

from isad.indexers.isad_new_catalog_indexer import ISADNewCatalogIndexer


@shared_task
def index_catalog_isad_record(isad_id):
    """
    Indexes an ISAD record in the catalog search index.

    This Celery task is triggered when an ISAD record is published or updated
    in a published state. It delegates the indexing logic to
    :class:`isad.indexers.isad_new_catalog_indexer.ISADNewCatalogIndexer`.

    Parameters
    ----------
    isad_id : int
        Primary key of the ISAD record to be indexed.

    Notes
    -----
    The task:
        - initializes the catalog indexer with the ISAD record ID
        - performs indexing using HTTP requests
        - commits the changes to the search index

    Executing this task asynchronously ensures that indexing does not block
    the main request/response cycle.
    """
    indexer = ISADNewCatalogIndexer(isad_id)
    indexer.index_with_requests()
    indexer.commit()


@shared_task
def index_catalog_isad_record_remove(isad_id):
    """
    Removes an ISAD record from the catalog search index.

    This Celery task is triggered when an ISAD record is unpublished or deleted.
    It delegates the removal logic to
    :class:`isad.indexers.isad_new_catalog_indexer.ISADNewCatalogIndexer`.

    Parameters
    ----------
    isad_id : int
        Primary key of the ISAD record to be removed from the index.

    Notes
    -----
    The removal is executed asynchronously to keep destructive or potentially
    slow index operations out of the synchronous application flow.
    """
    indexer = ISADNewCatalogIndexer(isad_id)
    indexer.delete()
