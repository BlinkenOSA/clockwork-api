from unittest import skip

from django.db.models.signals import post_save, pre_delete
from django.test import TestCase
from rest_framework.reverse import reverse

from catalog.views.statistics_views.archival_unit_sizes import ArchivalUnitSizes
from archival_unit.models import ArchivalUnit
from archival_unit.signals import update_isad_when_archival_unit_saved
from container.models import Container
from container.signals import update_finding_aids_index_upon_container_save
from finding_aids.models import FindingAidsEntity
from finding_aids.signals import remove_finding_aids_index, update_finding_aids_index
from isad.models import Isad
from isad.signals import remove_isad_index, update_isad_index


class _FixtureSignalsSafeTestCase(TestCase):
    fixtures = [
        "access_rights",
        "archival_unit_themes",
        "authority_genres_for_finding_aids",
        "finding_aids",
    ]

    @classmethod
    def setUpClass(cls):
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


class CatalogFixtureBackedViewTests(_FixtureSignalsSafeTestCase):
    @skip
    def test_archival_unit_sizes_endpoint_uses_real_records(self):
        response = ArchivalUnitSizes().get()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["reference_code"], "HU OSA 206")
        self.assertEqual(response.data[0]["size"], 3)

    @skip
    def test_archival_units_tree_quick_view_endpoint(self):
        response = self.client.get(reverse("catalog-v1:archival-units-tree-quick-view", args=[908]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reference_code"], "HU OSA 206-3-1")
        self.assertEqual(response.data["title"], "Audiovisual Recordings of Public Events")

    @skip
    def test_archival_units_tree_view_all_endpoint(self):
        response = self.client.get(reverse("catalog-v1:archival-units-tree", args=["all"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["reference_code"], "HU OSA 206")

        fonds_children = response.data[0]["children"]
        self.assertTrue(any(node["reference_code"] == "HU OSA 206-3" for node in fonds_children))

    @skip
    def test_finding_aids_entity_detail_endpoint(self):
        response = self.client.get(reverse("catalog-v1:finding-aids-full-view", args=["nOo1k70e"]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["catalog_id"], "nOo1k70e")
        self.assertEqual(response.data["archival_reference_code"], "HU OSA 206-3-1/3:1")

    @skip
    def test_finding_aids_entity_location_endpoint(self):
        response = self.client.get(reverse("catalog-v1:finding-aids-location-view", args=["nOo1k70e"]))

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 4)
        self.assertEqual(response.data[0]["reference_code"], "HU OSA 206")

    @skip
    def test_archival_units_detail_endpoint(self):
        response = self.client.get(reverse("catalog-v1:archival-units-full-view", args=[908]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["reference_code"], "HU OSA 206-3-1")
        self.assertEqual(response.data["archival_unit"]["title"], "Audiovisual Recordings of Public Events")
