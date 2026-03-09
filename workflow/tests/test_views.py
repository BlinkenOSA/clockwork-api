from django.contrib.auth.models import Group
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity


class WorkflowViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        api_group = Group.objects.create(name='Api')
        self.user.groups.add(api_group)

        fonds = ArchivalUnit.objects.create(fonds=1301, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1301,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1301,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_1301_1_1_0001',
            digital_version_exists=False,
        )

        self.fa = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            sequence_no=0,
            title='Folder',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
            legacy_id='LEGACY-1',
        )

    def test_get_set_digitized_container_retrieve(self):
        response = self.client.get(
            reverse('workflow-v1:list_set_digitized_container', kwargs={'barcode': self.container.barcode})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barcode'], self.container.barcode)

    def test_get_set_digitized_container_update(self):
        response = self.client.patch(
            reverse('workflow-v1:list_set_digitized_container', kwargs={'barcode': self.container.barcode}),
            data={
                'digital_version_exists': True,
                'digital_version_creation_date': '2024-01-01',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.container.refresh_from_db()
        self.assertTrue(self.container.digital_version_exists)

    def test_get_container_metadata(self):
        response = self.client.get(
            reverse('workflow-v1:list_get_container_metadata', kwargs={'barcode': self.container.barcode})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.fa.id)

    def test_get_container_by_legacy_id_from_finding_aids(self):
        response = self.client.get(
            reverse('workflow-v1:get_container_by_legacy_id', kwargs={'legacy_id': 'LEGACY-1'})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barcode'], self.container.barcode)

    def test_get_container_by_legacy_id_pattern(self):
        response = self.client.get(
            reverse('workflow-v1:get_container_by_legacy_id', kwargs={'legacy_id': 'HU_OSA_1301_1_1_0001_0001'})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['barcode'], self.container.barcode)

    def test_get_fa_entity_by_item_id(self):
        response = self.client.get(
            reverse('workflow-v1:get_fa_entity_by_item_id', kwargs={'item_id': 'HU_OSA_1301_1_1_0001_0001'})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['folder_no'], 1)
