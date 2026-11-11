from unittest.mock import patch

from django.test import SimpleTestCase

from finding_aids.models import FindingAidsEntity
from finding_aids.tasks import (
    index_catalog_finding_aids_entity,
    index_catalog_finding_aids_entity_remove,
    index_meilisearch_finding_aids_entity,
    index_meilisearch_finding_aids_entity_remove,
)


class FindingAidsTaskTests(SimpleTestCase):
    def test_catalog_index_task_ignores_missing_record(self):
        with patch(
            "finding_aids.tasks.FindingAidsNewCatalogIndexer",
            side_effect=FindingAidsEntity.DoesNotExist,
        ):
            index_catalog_finding_aids_entity(finding_aids_entity_id=12)

    def test_meilisearch_index_task_ignores_missing_record(self):
        with patch(
            "finding_aids.tasks.FindingAidsMeilisearchIndexer",
            side_effect=FindingAidsEntity.DoesNotExist,
        ):
            index_meilisearch_finding_aids_entity(finding_aids_entity_id=34)

    def test_catalog_remove_task_does_not_require_loading_record(self):
        with patch("finding_aids.tasks.FindingAidsNewCatalogIndexer") as mock_indexer_cls:
            mock_indexer = mock_indexer_cls.return_value

            index_catalog_finding_aids_entity_remove(finding_aids_entity_id=56, document_id="fa-doc-56")

        mock_indexer_cls.assert_called_once_with(56, load_record=False, document_id="fa-doc-56")
        mock_indexer.delete.assert_called_once_with()

    def test_meilisearch_remove_task_does_not_require_loading_record(self):
        with patch("finding_aids.tasks.FindingAidsMeilisearchIndexer") as mock_indexer_cls:
            mock_indexer = mock_indexer_cls.return_value

            index_meilisearch_finding_aids_entity_remove(finding_aids_entity_id=78, document_id="fa-doc-78")

        mock_indexer_cls.assert_called_once_with(78, load_record=False, document_id="fa-doc-78", target="ams")
        mock_indexer.delete.assert_called_once_with()

    def test_meilisearch_index_task_selects_target(self):
        for target in ("ams", "catalog"):
            with self.subTest(target=target), patch(
                "finding_aids.tasks.FindingAidsMeilisearchIndexer"
            ) as indexer_class:
                index_meilisearch_finding_aids_entity(finding_aids_entity_id=34, target=target)

                indexer_class.assert_called_once_with(34, target=target)
                indexer_class.return_value.index.assert_called_once_with()

    def test_meilisearch_remove_task_selects_catalog_target(self):
        with patch("finding_aids.tasks.FindingAidsMeilisearchIndexer") as indexer_class:
            index_meilisearch_finding_aids_entity_remove(
                finding_aids_entity_id=78, document_id="fa-doc-78", target="catalog"
            )

        indexer_class.assert_called_once_with(
            78, load_record=False, document_id="fa-doc-78", target="catalog"
        )
        indexer_class.return_value.delete.assert_called_once_with()
