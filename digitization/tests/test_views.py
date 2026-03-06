from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity


class DigitizationViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        self.init()
        fonds = ArchivalUnit.objects.create(fonds=800, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=800,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=800,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )

        self.container_yes = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_A',
            digital_version_exists=True,
            digital_version_online=True,
            digital_version_technical_metadata='{"streams":[]}',
        )
        self.container_no = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            barcode='HU_OSA_B',
            digital_version_exists=False,
            digital_version_online=False,
        )

        self.fa_yes = FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container_yes,
            folder_no=1,
            primary_type=PrimaryType.objects.first(),
            title='Digitized folder',
            date_from='2020-01-01',
            digital_version_exists=True,
            digital_version_online=True,
            digital_version_technical_metadata='{"streams":[]}',
        )
        FindingAidsEntity.objects.create(
            archival_unit=self.series,
            container=self.container_yes,
            folder_no=2,
            primary_type=PrimaryType.objects.first(),
            title='Non-online folder',
            date_from='2020-01-01',
            digital_version_exists=True,
            digital_version_online=False,
        )

    def test_container_list_filters_digital_version_exists(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-list'),
            {'digital_version_exists': 'yes'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row['id'] for row in response.data['results']}
        self.assertEqual(ids, {self.container_yes.id})

    def test_container_detail_returns_metadata_field(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-detail', kwargs={'pk': self.container_yes.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('digital_version_technical_metadata', response.data)

    def test_finding_aids_list_filters_digital_version_online(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-finding_aids-list'),
            {'digital_version_online': 'yes'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row['id'] for row in response.data['results']}
        self.assertEqual(ids, {self.fa_yes.id})

    def test_finding_aids_detail_returns_metadata_field(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-finding_aids-detail', kwargs={'pk': self.fa_yes.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('digital_version_technical_metadata', response.data)
