from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity


class FindingAidsExtraViewsTests(NoIndexSignalsMixin, TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        fonds = ArchivalUnit.objects.create(fonds=901, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=901,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=901,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            container_no=1,
            digital_version_exists=True,
            digital_version_online=True,
            digital_version_research_cloud=True,
            digital_version_research_cloud_path='s3://bucket/path',
            barcode='HU_OSA_TEST',
        )

        subfonds_other = ArchivalUnit.objects.create(
            fonds=901,
            subfonds=2,
            level='SF',
            title='Other Subfonds',
            parent=fonds,
        )
        self.other_series = ArchivalUnit.objects.create(
            fonds=901,
            subfonds=2,
            series=1,
            level='S',
            title='Other Series',
            parent=subfonds_other,
        )
        self.other_container = Container.objects.create(
            archival_unit=self.other_series,
            carrier_type=CarrierType.objects.first(),
            container_no=2,
        )

        self.l1 = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            description_level='L1',
            level='F',
            folder_no=1,
            title='Folder',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )
        self.l2 = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            description_level='L2',
            level='I',
            folder_no=1,
            sequence_no=1,
            title='Item',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )
        self.other_l1 = FindingAidsEntity.objects.create(
            archival_unit=self.other_series,
            container=self.other_container,
            description_level='L1',
            level='F',
            folder_no=1,
            title='Other Folder',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )

    def test_pre_create_returns_container_digitization_flags(self):
        response = self.client.get(
            reverse('finding_aids-v1:finding_aids-pre-create', kwargs={'container_id': self.container.id}),
            {'description_level': 'L1', 'level': 'F'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['container_id'], self.container.id)
        self.assertTrue(response.data['digital_version_exists_container']['digital_version'])

    def test_get_next_folder_l1_and_l2(self):
        response_l1 = self.client.get(
            reverse('finding_aids-v1:finding_aids-get-next-folder', kwargs={'container_id': self.container.id}),
            {'description_level': 'L1'},
        )
        self.assertEqual(response_l1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_l1.data['folder_no'], 3)
        self.assertEqual(response_l1.data['sequence_no'], 0)

        response_l2 = self.client.get(
            reverse('finding_aids-v1:finding_aids-get-next-folder', kwargs={'container_id': self.container.id}),
            {'description_level': 'L2', 'folder_no': 1},
        )
        self.assertEqual(response_l2.status_code, status.HTTP_200_OK)
        self.assertEqual(response_l2.data['folder_no'], '1')
        self.assertEqual(response_l2.data['sequence_no'], 2)

    def test_template_pre_create(self):
        response = self.client.get(
            reverse('finding_aids-v1:finding_aids-template-pre-create', kwargs={'series_id': self.series.id})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['archival_unit'], self.series.id)
        self.assertEqual(response.data['description_level'], 'L1')
        self.assertTrue(response.data['is_template'])
        self.assertTrue(response.data['archival_reference_code'].endswith('-TEMPLATE'))

    def test_action_set_and_unset_confidential(self):
        response = self.client.put(
            reverse('finding_aids-v1:finding_aids-publish', kwargs={'action': 'set_confidential', 'pk': self.l1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.l1.refresh_from_db()
        self.assertTrue(self.l1.confidential)

        response = self.client.put(
            reverse('finding_aids-v1:finding_aids-publish', kwargs={'action': 'set_non_confidential', 'pk': self.l1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.l1.refresh_from_db()
        self.assertFalse(self.l1.confidential)

    def test_action_set_and_unset_missing(self):
        response = self.client.put(
            reverse('finding_aids-v1:finding_aids-publish', kwargs={'action': 'set_missing', 'pk': self.l1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.l1.refresh_from_db()
        self.assertTrue(self.l1.missing)

        response = self.client.put(
            reverse('finding_aids-v1:finding_aids-publish', kwargs={'action': 'set_non_missing', 'pk': self.l1.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.l1.refresh_from_db()
        self.assertFalse(self.l1.missing)

    def test_missing_list_returns_only_missing_entities(self):
        self.l1.missing = True
        self.l1.save()

        response = self.client.get(
            reverse('finding_aids-v1:finding_aids-missing-list')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.l1.id)
        self.assertTrue(response.data['results'][0]['missing'])

    def test_missing_list_filters_by_archival_unit_id(self):
        self.l1.missing = True
        self.l1.save()
        self.other_l1.missing = True
        self.other_l1.save()

        response = self.client.get(
            reverse('finding_aids-v1:finding_aids-missing-list'),
            {'archival_unit_id': self.series.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], self.l1.id)

    def test_missing_series_select_returns_only_series_with_missing_entities(self):
        self.l1.missing = True
        self.l1.save()

        response = self.client.get(
            reverse('finding_aids-v1:finding_aids-missing-series-select')
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.series.id)
        self.assertEqual(response.data[0]['title'], self.series.title)
