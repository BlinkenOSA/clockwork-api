from django.contrib.auth.models import Group
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity
from isad.models import Isad


@override_settings(CATALOG_URL='https://catalog.example')
class DigitalObjectJSONViewTests(NoIndexSignalsMixin, TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        api_group = Group.objects.create(name='Api')
        self.user.groups.add(api_group)

        self.fonds = ArchivalUnit.objects.create(fonds=305, level='F', title='Fonds Title')
        self.subfonds = ArchivalUnit.objects.create(
            fonds=305,
            subfonds=1,
            level='SF',
            title='Subfonds Title',
            parent=self.fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=305,
            subfonds=1,
            series=1,
            level='S',
            title='Series Title',
            parent=self.subfonds,
        )

        Isad.objects.create(
            archival_unit=self.fonds,
            title=self.fonds.title,
            reference_code=self.fonds.reference_code,
            description_level='F',
            year_from=1900,
        )
        Isad.objects.create(
            archival_unit=self.subfonds,
            title=self.subfonds.title,
            reference_code=self.subfonds.reference_code,
            description_level='SF',
            year_from=1901,
        )
        Isad.objects.create(
            archival_unit=self.series,
            title=self.series.title,
            reference_code=self.series.reference_code,
            description_level='S',
            year_from=1902,
        )

        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_305_1_1_0001',
            legacy_id='LEG-305-1',
        )

        self.folder = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            sequence_no=0,
            title='Folder Title',
            date_from='2020-01-01',
            primary_type=PrimaryType.objects.first(),
        )
        self.item = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            sequence_no=1,
            title='Item Title',
            level='I',
            description_level='L2',
            date_from='2020-01-02',
            primary_type=PrimaryType.objects.first(),
        )

    def test_digital_object_json_invalid_filename(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_json', kwargs={'file_name': 'invalid_name.txt'})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid filename'})

    def test_digital_object_json_returns_container_hierarchy_and_all_entities(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_json', kwargs={'file_name': 'HU_OSA_305_1_1_0001.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['fonds']['title'], self.fonds.title)
        self.assertEqual(response.data['fonds']['isad']['description_level'], 'F')
        self.assertEqual(response.data['subfonds']['title'], self.subfonds.title)
        self.assertEqual(response.data['series']['title'], self.series.title)
        self.assertEqual(response.data['container']['container_no'], self.container.container_no)
        self.assertEqual(response.data['container']['carrier_type'], self.container.carrier_type.type)
        self.assertEqual(response.data['container']['legacy_id'], self.container.legacy_id)
        self.assertEqual(response.data['container']['barcode'], self.container.barcode)
        self.assertEqual(len(response.data['finding_aids_entities']), 2)
        self.assertEqual(
            [row['archival_reference_code'] for row in response.data['finding_aids_entities']],
            [self.folder.archival_reference_code, self.item.archival_reference_code]
        )

    def test_digital_object_json_returns_single_matching_finding_aids_entity(self):
        response = self.client.get(
            reverse(
                'workflow-v1:digital_object_json',
                kwargs={'file_name': 'HU_OSA_305_1_1_0001_0001_0001.mp4'}
            )
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['series']['reference_code'], self.series.reference_code)
        self.assertEqual(response.data['container']['barcode'], self.container.barcode)
        self.assertEqual(len(response.data['finding_aids_entities']), 1)
        self.assertEqual(
            response.data['finding_aids_entities'][0]['archival_reference_code'],
            self.item.archival_reference_code
        )
