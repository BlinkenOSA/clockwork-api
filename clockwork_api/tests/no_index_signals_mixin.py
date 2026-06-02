from django.db.models.signals import post_save, pre_delete
from unittest.mock import patch

from archival_unit.models import ArchivalUnit
from archival_unit.signals import update_isad_when_archival_unit_saved
from container.models import Container
from container.signals import update_finding_aids_index_upon_container_save
from finding_aids.models import FindingAidsEntity
from finding_aids.signals import remove_finding_aids_index, update_finding_aids_index
from isad.models import Isad
from isad.signals import remove_isad_index, update_isad_index


class NoIndexSignalsMixin:
    """
    Disables search indexing signals for tests that do not assert indexing behavior.
    """

    @classmethod
    def setUpClass(cls):
        cls._index_task_patchers = [
            patch('finding_aids.tasks.index_catalog_finding_aids_entity.delay'),
            patch('finding_aids.tasks.index_catalog_finding_aids_entity_remove.delay'),
            patch('finding_aids.tasks.index_meilisearch_finding_aids_entity.delay'),
            patch('finding_aids.tasks.index_meilisearch_finding_aids_entity_remove.delay'),
            patch('isad.tasks.index_catalog_isad_record.delay'),
            patch('isad.tasks.index_catalog_isad_record_remove.delay'),
            patch('isad.tasks.index_meilisearch_isad_record.delay'),
            patch('isad.tasks.index_meilisearch_isad_record_remove.delay'),
        ]
        for patcher in cls._index_task_patchers:
            patcher.start()

        post_save.disconnect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.disconnect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.disconnect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.disconnect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        post_save.disconnect(update_isad_index, sender=Isad)
        pre_delete.disconnect(remove_isad_index, sender=Isad)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(update_finding_aids_index, sender=FindingAidsEntity)
        pre_delete.connect(remove_finding_aids_index, sender=FindingAidsEntity)
        post_save.connect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.connect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        post_save.connect(update_isad_index, sender=Isad)
        pre_delete.connect(remove_isad_index, sender=Isad)
        for patcher in reversed(getattr(cls, '_index_task_patchers', [])):
            patcher.stop()
