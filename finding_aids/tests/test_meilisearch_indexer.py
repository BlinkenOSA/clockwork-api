from types import SimpleNamespace
from unittest.mock import patch

from django.core.exceptions import ImproperlyConfigured
from django.test import SimpleTestCase, override_settings

from finding_aids.indexers.finding_aids_meilisearch_indexer import FindingAidsMeilisearchIndexer


@override_settings(
    MEILISEARCH_URL="http://meilisearch.test:7700",
    MEILISEARCH_AMS_API_KEY="ams-key",
    MEILISEARCH_AMS_INDEX="ams-index",
    MEILISEARCH_CATALOG_API_KEY="catalog-key",
    MEILISEARCH_CATALOG_INDEX="catalog-test-index",
)
class FindingAidsMeilisearchIndexerTests(SimpleTestCase):
    @patch("finding_aids.indexers.finding_aids_meilisearch_indexer.meilisearch.Client")
    def test_index_and_delete_use_selected_destination(self, client_class):
        record = SimpleNamespace(
            id=42,
            catalog_id="fa-doc-42",
            archival_unit=SimpleNamespace(id=10, reference_code="HU OSA 1-1-1"),
            archival_reference_code="HU OSA 1-1-1:1/1",
            published=False,
            title="Folder title",
            title_original="",
            primary_type=None,
            level="F",
            contents_summary="<p>Folder contents</p>",
            contents_summary_original="",
        )
        for target, key, index_name in (
            ("ams", "ams-key", "ams-index"),
            ("catalog", "catalog-key", "catalog-test-index"),
        ):
            with self.subTest(target=target), patch.object(
                FindingAidsMeilisearchIndexer, "_get_finding_aids_record", return_value=record
            ):
                client_class.reset_mock()
                indexer = FindingAidsMeilisearchIndexer(42, target=target)
                indexer.index()
                indexer.delete()

                client_class.assert_called_once_with("http://meilisearch.test:7700", key)
                client_class.return_value.index.assert_called_once_with(index_name)
                index = client_class.return_value.index.return_value
                index.add_documents.assert_called_once_with([indexer.doc])
                self.assertEqual(indexer.doc["id"], "fa-doc-42")
                self.assertEqual(indexer.doc["contents_summary"], "Folder contents")
                index.delete_document.assert_called_once_with(document_id="fa-doc-42")

    @patch("finding_aids.indexers.finding_aids_meilisearch_indexer.meilisearch.Client")
    def test_default_destination_is_ams(self, client_class):
        FindingAidsMeilisearchIndexer(42, load_record=False)

        client_class.assert_called_once_with("http://meilisearch.test:7700", "ams-key")
        client_class.return_value.index.assert_called_once_with("ams-index")

    @patch("finding_aids.indexers.finding_aids_meilisearch_indexer.meilisearch.Client")
    def test_catalog_requires_its_own_configuration(self, client_class):
        for setting_name in ("MEILISEARCH_CATALOG_API_KEY", "MEILISEARCH_CATALOG_INDEX"):
            with self.subTest(setting=setting_name), override_settings(**{setting_name: ""}):
                with self.assertRaisesMessage(ImproperlyConfigured, "Catalog indexing requires"):
                    FindingAidsMeilisearchIndexer(42, load_record=False, target="catalog")

        client_class.assert_not_called()

    @patch("finding_aids.indexers.finding_aids_meilisearch_indexer.meilisearch.Client")
    def test_invalid_target_fails_before_connecting(self, client_class):
        with self.assertRaisesMessage(ValueError, "Meilisearch target must be 'ams' or 'catalog'."):
            FindingAidsMeilisearchIndexer(42, load_record=False, target="unknown")

        client_class.assert_not_called()

    @patch("finding_aids.indexers.finding_aids_meilisearch_indexer.meilisearch.Client")
    def test_catalog_deletion_does_not_load_deleted_record(self, client_class):
        indexer = FindingAidsMeilisearchIndexer(
            42, load_record=False, document_id="deleted-doc", target="catalog"
        )
        indexer.delete()

        client_class.return_value.index.assert_called_once_with("catalog-test-index")
        client_class.return_value.index.return_value.delete_document.assert_called_once_with(
            document_id="deleted-doc"
        )
