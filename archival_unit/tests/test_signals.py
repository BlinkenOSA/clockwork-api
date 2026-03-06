from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from archival_unit.signals import update_isad_when_archival_unit_saved


class UpdateIsadSignalTests(SimpleTestCase):
    def test_no_isad_relation_does_not_enqueue_tasks(self):
        instance = SimpleNamespace()

        with patch("archival_unit.signals.index_catalog_isad_record.delay") as mock_index_delay, patch(
            "archival_unit.signals.index_catalog_isad_record_remove.delay"
        ) as mock_remove_delay:
            update_isad_when_archival_unit_saved(sender=None, instance=instance)

        mock_index_delay.assert_not_called()
        mock_remove_delay.assert_not_called()

    def test_published_isad_enqueues_reindex(self):
        instance = SimpleNamespace(isad=SimpleNamespace(id=42, published=True))

        with patch("archival_unit.signals.index_catalog_isad_record.delay") as mock_index_delay, patch(
            "archival_unit.signals.index_catalog_isad_record_remove.delay"
        ) as mock_remove_delay:
            update_isad_when_archival_unit_saved(sender=None, instance=instance)

        mock_index_delay.assert_called_once_with(isad_id=42)
        mock_remove_delay.assert_not_called()

    def test_unpublished_isad_enqueues_remove(self):
        instance = SimpleNamespace(isad=SimpleNamespace(id=77, published=False))

        with patch("archival_unit.signals.index_catalog_isad_record.delay") as mock_index_delay, patch(
            "archival_unit.signals.index_catalog_isad_record_remove.delay"
        ) as mock_remove_delay:
            update_isad_when_archival_unit_saved(sender=None, instance=instance)

        mock_remove_delay.assert_called_once_with(isad_id=77)
        mock_index_delay.assert_not_called()
