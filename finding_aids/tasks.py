# Create your tasks here
from celery import shared_task
from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer


@shared_task
def index_catalog_finding_aids_entity(finding_aids_entity_id):
    """
    Indexes a finding aids entity in the catalog search index.

    This task:
        1. Instantiates the catalog indexer for the given entity
        2. Indexes the entity metadata
        3. Commits the changes to the search backend

    The task is typically triggered by:
        - publication of a finding aids entity
        - updates to a published entity
    """
    indexer = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer.index()
    indexer.commit()


@shared_task
def index_catalog_finding_aids_entity_remove(finding_aids_entity_id):
    """
    Removes a finding aids entity from the catalog search index.

    This task is typically triggered when:
        - an entity is unpublished
        - an entity is deleted

    The index removal is performed asynchronously to avoid blocking
    request/response cycles.
    """
    indexer = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    indexer.delete()

