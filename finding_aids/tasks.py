from celery import shared_task

from finding_aids.indexers.finding_aids_meilisearch_indexer import FindingAidsMeilisearchIndexer
from finding_aids.indexers.finding_aids_new_catalog_indexer import FindingAidsNewCatalogIndexer
from finding_aids.models import FindingAidsEntity


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
    try:
        indexer = FindingAidsNewCatalogIndexer(finding_aids_entity_id)
    except FindingAidsEntity.DoesNotExist:
        return
    indexer.index()
    indexer.commit()


@shared_task
def index_catalog_finding_aids_entity_remove(finding_aids_entity_id, document_id=None):
    """
    Removes a finding aids entity from the catalog search index.

    This task is typically triggered when:
        - an entity is unpublished
        - an entity is deleted

    The index removal is performed asynchronously to avoid blocking
    request/response cycles.
    """
    indexer = FindingAidsNewCatalogIndexer(
        finding_aids_entity_id,
        load_record=False,
        document_id=document_id,
    )
    indexer.delete()


@shared_task
def index_meilisearch_finding_aids_entity(finding_aids_entity_id, target="ams"):
    """
    Indexes a finding aids entity in the selected Meilisearch target.
    """
    try:
        indexer = FindingAidsMeilisearchIndexer(finding_aids_entity_id, target=target)
    except FindingAidsEntity.DoesNotExist:
        return
    indexer.index()


@shared_task
def index_meilisearch_finding_aids_entity_remove(finding_aids_entity_id, document_id=None, target="ams"):
    """
    Removes a finding aids entity from the selected Meilisearch target.
    """
    indexer = FindingAidsMeilisearchIndexer(
        finding_aids_entity_id,
        load_record=False,
        document_id=document_id,
        target=target,
    )
    indexer.delete()
