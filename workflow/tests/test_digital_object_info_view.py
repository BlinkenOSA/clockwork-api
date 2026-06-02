from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.reverse import reverse
from xml.etree import ElementTree

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity
from isad.models import Isad
from workflow.serializers.container_serializers import ContainerDigitizedSerializer
from workflow.serializers.finding_aids_serializer import FindingAidsDigitizedSerializer


@override_settings(CATALOG_URL='https://catalog.example')
class DigitalObjectInfoViewTests(NoIndexSignalsMixin, TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        api_group = Group.objects.create(name='Api')
        self.user.groups.add(api_group)

        fonds = ArchivalUnit.objects.create(fonds=1301, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=301,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=301,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        Isad.objects.create(
            archival_unit=self.series,
            title=self.series.title,
            reference_code=self.series.reference_code,
            description_level='S',
            year_from=1900,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_301_1_1_0001',
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
        )

    def test_digital_object_info_invalid_filename(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_info', kwargs={'file_name': 'invalid_name.txt'})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid filename'})

    def test_digital_object_info_returns_container_serializer_payload(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_info', kwargs={'file_name': 'HU_OSA_301_1_1_0001.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['level'], 'Container')
        self.assertEqual(response.data['container']['barcode'], self.container.barcode)
        self.assertEqual(response.data['container']['container_no'], self.container.container_no)

    def test_digital_object_info_returns_finding_aids_serializer_payload(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_info', kwargs={'file_name': 'HU_OSA_301_1_1_0001_0001.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['level'], 'Folder / Item')
        self.assertEqual(response.data['container']['barcode'], self.container.barcode)

    def test_digital_object_info_valid_pattern_but_unresolvable(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_info', kwargs={'file_name': 'HU_OSA_301_1_1_0001_9999.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


@override_settings(CATALOG_URL='https://catalog.example')
class DigitalObjectEADViewTests(NoIndexSignalsMixin, TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        api_group = Group.objects.create(name='Api')
        self.user.groups.add(api_group)

        self.fonds = ArchivalUnit.objects.create(fonds=303, level='F', title='Fonds Title')
        self.subfonds = ArchivalUnit.objects.create(
            fonds=303,
            subfonds=1,
            level='SF',
            title='Subfonds Title',
            parent=self.fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=303,
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
            year_from=1945,
            year_to=1950,
            scope_and_content_abstract='Fonds scope',
            administrative_history='Fonds history',
        )
        Isad.objects.create(
            archival_unit=self.subfonds,
            title=self.subfonds.title,
            reference_code=self.subfonds.reference_code,
            description_level='SF',
            year_from=1945,
            year_to=1949,
            scope_and_content_abstract='Subfonds scope',
        )
        Isad.objects.create(
            archival_unit=self.series,
            title=self.series.title,
            reference_code=self.series.reference_code,
            description_level='S',
            year_from=1946,
            year_to=1948,
            scope_and_content_abstract='Series scope',
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_303_1_1_0001',
            internal_note='Container note',
            digital_version_exists=True,
            digital_version_online=True,
        )

        self.folder = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            sequence_no=0,
            title='Folder Title',
            date_from='2020-01-01',
            contents_summary='Folder scope',
            note='Folder note',
            primary_type=PrimaryType.objects.first(),
        )
        self.item = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container,
            folder_no=1,
            sequence_no=1,
            level='I',
            description_level='L2',
            title='Item Title',
            date_from='2020-01-02',
            contents_summary='Item scope',
            primary_type=PrimaryType.objects.first(),
        )

    def test_digital_object_ead_invalid_filename(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_ead', kwargs={'file_name': 'invalid_name.txt'})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {'error': 'Invalid filename'})

    def test_digital_object_ead_returns_container_hierarchy_with_all_entities(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_ead', kwargs={'file_name': 'HU_OSA_303_1_1_0001.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response['Content-Type'].startswith('application/xml'))

        xml = response.content.decode('utf-8')
        self.assertIn('Fonds Title', xml)
        self.assertIn('Subfonds Title', xml)
        self.assertIn('Series Title', xml)
        self.assertIn('Subfonds scope', xml)
        self.assertIn('Series scope', xml)
        self.assertIn('Container note', xml)
        self.assertIn('Folder Title', xml)
        self.assertIn('Item Title', xml)

        root = ElementTree.fromstring(xml)
        ns = {'ead': 'urn:isbn:1-931666-22-9'}
        self.assertEqual(root.tag, '{urn:isbn:1-931666-22-9}ead')
        self.assertEqual(len(root.findall(".//ead:c[@otherlevel='container']", ns)), 1)
        self.assertEqual(len(root.findall(".//ead:c[@level='file']", ns)), 1)
        self.assertEqual(len(root.findall(".//ead:c[@level='item']", ns)), 1)

    def test_digital_object_ead_returns_single_requested_finding_aids_entity(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_ead', kwargs={'file_name': 'HU_OSA_303_1_1_0001_0001_0001.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        xml = response.content.decode('utf-8')
        self.assertIn('Fonds Title', xml)
        self.assertIn('Subfonds Title', xml)
        self.assertIn('Series Title', xml)
        self.assertIn('Item Title', xml)
        self.assertNotIn('Folder scope', xml)

        root = ElementTree.fromstring(xml)
        ns = {'ead': 'urn:isbn:1-931666-22-9'}
        self.assertEqual(len(root.findall(".//ead:c[@level='item']", ns)), 1)
        self.assertEqual(len(root.findall(".//ead:c[@level='file']", ns)), 0)


@override_settings(CATALOG_URL='https://catalog.example')
class WorkflowDigitizedSerializersTests(NoIndexSignalsMixin, TestCase):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        fonds = ArchivalUnit.objects.create(fonds=302, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=302,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=302,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        Isad.objects.create(
            archival_unit=self.series,
            title=self.series.title,
            reference_code=self.series.reference_code,
            description_level='S',
            year_from=1900,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_302_1_1_0001',
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
            published=True,
        )

    def test_container_digitized_serializer_shape(self):
        data = ContainerDigitizedSerializer(self.container).data

        self.assertEqual(data['level'], 'Container')
        self.assertIn('archival_reference_code', data)
        self.assertIn('container', data)
        self.assertIn('digital_versions', data)

    def test_finding_aids_digitized_serializer_shape(self):
        data = FindingAidsDigitizedSerializer(self.fa).data

        self.assertEqual(data['level'], 'Folder / Item')
        self.assertIn('archival_reference_code', data)
        self.assertIn('container', data)
        self.assertIn('digital_versions', data)
