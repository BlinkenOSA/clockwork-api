from unittest import skip

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types, make_primary_types, make_access_rights
from finding_aids.tests.helpers import make_finding_aids


class DigitizationViewsTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types(type='VHS')
        self.primary_type = make_primary_types(type='Moving Image')
        self.access_rights = make_access_rights()

        self.container_yes = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_A',
            digital_version_exists=True,
            digital_version_online=True,
            digital_version_technical_metadata='{"streams":[]}',
        )
        self.container_no = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_B',
            digital_version_exists=False,
            digital_version_online=False,
        )

        self.fa_yes = make_finding_aids(
            container=self.container_yes,
            access_rights=self.access_rights,
            folder_no=1,
            primary_type=self.primary_type,
            title='Digitized folder',
            date_from='2020-01-01',
            digital_version_exists=True,
            digital_version_online=True,
            digital_version_technical_metadata='{"streams":[]}',
        )
        make_finding_aids(
            container=self.container_yes,
            access_rights=self.access_rights,
            folder_no=2,
            primary_type=self.primary_type,
            title='Non-online folder',
            date_from='2020-01-01',
            digital_version_exists=True,
            digital_version_online=False,
        )

    @skip
    def test_container_list_filters_digital_version_exists(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-list'),
            {'digital_version_exists': 'yes'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = {row['id'] for row in response.data['results']}
        self.assertEqual(ids, {self.container_yes.id})

    @skip
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
