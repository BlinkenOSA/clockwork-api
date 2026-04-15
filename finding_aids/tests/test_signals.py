from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from finding_aids.signals import remove_finding_aids_index, update_finding_aids_index


class FindingAidsSignalTests(SimpleTestCase):
    def test_update_finding_aids_index_published_enqueues_catalog_and_meili_index(self):
        instance = SimpleNamespace(id=42, published=True, catalog_id="fa-doc-42")

        with patch("finding_aids.signals.index_catalog_finding_aids_entity.delay") as mock_catalog_index_delay, patch(
            "finding_aids.signals.index_catalog_finding_aids_entity_remove.delay"
        ) as mock_catalog_remove_delay, patch(
            "finding_aids.signals.index_meilisearch_finding_aids_entity.delay"
        ) as mock_meili_index_delay, patch(
            "finding_aids.signals.index_meilisearch_finding_aids_entity_remove.delay"
        ) as mock_meili_remove_delay:
            update_finding_aids_index(sender=None, instance=instance)

        mock_catalog_index_delay.assert_called_once_with(finding_aids_entity_id=42)
        mock_catalog_remove_delay.assert_not_called()
        mock_meili_index_delay.assert_called_once_with(finding_aids_entity_id=42)
        mock_meili_remove_delay.assert_not_called()

    def test_update_finding_aids_index_unpublished_enqueues_catalog_remove_and_meili_index(self):
        instance = SimpleNamespace(id=77, published=False, catalog_id="fa-doc-77")

        with patch("finding_aids.signals.index_catalog_finding_aids_entity.delay") as mock_catalog_index_delay, patch(
            "finding_aids.signals.index_catalog_finding_aids_entity_remove.delay"
        ) as mock_catalog_remove_delay, patch(
            "finding_aids.signals.index_meilisearch_finding_aids_entity.delay"
        ) as mock_meili_index_delay, patch(
            "finding_aids.signals.index_meilisearch_finding_aids_entity_remove.delay"
        ) as mock_meili_remove_delay:
            update_finding_aids_index(sender=None, instance=instance)

        mock_catalog_index_delay.assert_not_called()
        mock_catalog_remove_delay.assert_called_once_with(finding_aids_entity_id=77)
        mock_meili_index_delay.assert_called_once_with(finding_aids_entity_id=77)
        mock_meili_remove_delay.assert_not_called()

    def test_remove_finding_aids_index_enqueues_catalog_and_meili_remove(self):
        instance = SimpleNamespace(id=15, catalog_id="fa-doc-15")

        with patch("finding_aids.signals.index_catalog_finding_aids_entity_remove.delay") as mock_catalog_remove_delay, patch(
            "finding_aids.signals.index_meilisearch_finding_aids_entity_remove.delay"
        ) as mock_meili_remove_delay:
            remove_finding_aids_index(sender=None, instance=instance)

        mock_catalog_remove_delay.assert_called_once_with(finding_aids_entity_id=15)
        mock_meili_remove_delay.assert_called_once_with(finding_aids_entity_id=15,)
