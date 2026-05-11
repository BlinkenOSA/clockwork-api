from django.contrib.auth.models import Group
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity
from isad.models import Isad
from workflow.serializers.container_serializers import ContainerDigitizedSerializer
from workflow.serializers.finding_aids_serializer import FindingAidsDigitizedSerializer


@override_settings(CATALOG_URL='https://catalog.example')
class DigitalObjectInfoViewTests(TestViewsBaseClass):
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
        self.assertEqual(response.data['metadata']['folder_no'], self.fa.folder_no)

    def test_digital_object_info_valid_pattern_but_unresolvable(self):
        response = self.client.get(
            reverse('workflow-v1:digital_object_info', kwargs={'file_name': 'HU_OSA_301_1_1_0001_9999.mp4'})
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)


@override_settings(CATALOG_URL='https://catalog.example')
class WorkflowDigitizedSerializersTests(TestCase):
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
        self.assertIn('metadata', data)
        self.assertIn('digital_versions', data)

    def test_finding_aids_digitized_serializer_shape(self):
        data = FindingAidsDigitizedSerializer(self.fa).data

        self.assertEqual(data['level'], 'Folder / Item')
        self.assertIn('archival_reference_code', data)
        self.assertIn('container', data)
        self.assertIn('metadata', data)
        self.assertIn('digital_versions', data)
