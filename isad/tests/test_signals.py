from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from isad.signals import remove_isad_index, update_isad_index


class IsadSignalTests(SimpleTestCase):
    def test_update_isad_index_published_enqueues_catalog_and_meili_index(self):
        instance = SimpleNamespace(id=42, published=True, catalog_id="abc123")

        with patch("isad.signals.index_catalog_isad_record.delay") as mock_catalog_index_delay, patch(
            "isad.signals.index_catalog_isad_record_remove.delay"
        ) as mock_catalog_remove_delay, patch(
            "isad.signals.index_meilisearch_isad_record.delay"
        ) as mock_meili_index_delay, patch(
            "isad.signals.index_meilisearch_isad_record_remove.delay"
        ) as mock_meili_remove_delay:
            update_isad_index(sender=None, instance=instance)

        mock_catalog_index_delay.assert_called_once_with(isad_id=42)
        mock_catalog_remove_delay.assert_not_called()
        mock_meili_index_delay.assert_called_once_with(isad_id=42)
        mock_meili_remove_delay.assert_not_called()

    def test_update_isad_index_unpublished_enqueues_catalog_remove_and_meili_index(self):
        instance = SimpleNamespace(id=77, published=False, catalog_id="isad-doc-77")

        with patch("isad.signals.index_catalog_isad_record.delay") as mock_catalog_index_delay, patch(
            "isad.signals.index_catalog_isad_record_remove.delay"
        ) as mock_catalog_remove_delay, patch(
            "isad.signals.index_meilisearch_isad_record.delay"
        ) as mock_meili_index_delay, patch(
            "isad.signals.index_meilisearch_isad_record_remove.delay"
        ) as mock_meili_remove_delay:
            update_isad_index(sender=None, instance=instance)

        mock_catalog_index_delay.assert_not_called()
        mock_catalog_remove_delay.assert_called_once_with(isad_id=77)
        mock_meili_index_delay.assert_called_once_with(isad_id=77)
        mock_meili_remove_delay.assert_not_called()

    def test_remove_isad_index_enqueues_catalog_and_meili_remove(self):
        instance = SimpleNamespace(id=15, catalog_id="isad-doc-15")

        with patch("isad.signals.index_catalog_isad_record_remove.delay") as mock_catalog_remove_delay, patch(
            "isad.signals.index_meilisearch_isad_record_remove.delay"
        ) as mock_meili_remove_delay:
            remove_isad_index(sender=None, instance=instance)

        mock_catalog_remove_delay.assert_called_once_with(isad_id=15)
        mock_meili_remove_delay.assert_called_once_with(isad_id=15)