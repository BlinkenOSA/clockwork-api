# Create your tasks here
import meilisearch
from celery import shared_task
from django.conf import settings

from finding_aids.indexers.finding_aids_meilisearch_indexer import FindingMeilisearchIndexer
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


def _get_meilisearch_index():
    meilisearch_url = getattr(settings, 'MEILISEARCH_URL', '')
    meilisearch_api_key = getattr(settings, 'MEILISEARCH_API_KEY', '')
    index_name = getattr(settings, 'MEILISEARCH_INDEX', 'catalog')
    client = meilisearch.Client(meilisearch_url, meilisearch_api_key)
    return client.index(index_name)


@shared_task
def index_meilisearch_finding_aids_entity(finding_aids_entity_id):
    """
    Indexes a finding aids entity in Meilisearch.
    """
    indexer = FindingMeilisearchIndexer(finding_aids_entity_id)
    indexer.index()


@shared_task
def index_meilisearch_finding_aids_entity_remove(finding_aids_entity_id):
    """
    Removes a finding aids entity in Meilisearch.
    """
    indexer = FindingMeilisearchIndexer(finding_aids_entity_id)
    indexer.delete()