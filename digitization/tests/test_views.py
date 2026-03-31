from unittest import skip

from django.db.models.signals import post_save
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from archival_unit.signals import update_isad_when_archival_unit_saved
from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from container.signals import update_finding_aids_index_upon_container_save
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types, make_primary_types, make_access_rights
from digitization.tests.helpers import make_digital_version_container, get_tech_md
from finding_aids.models import FindingAidsEntity
from finding_aids.signals import update_finding_aids_index
from finding_aids.tests.helpers import make_finding_aids


class DigitizationViewsTests(TestViewsBaseClass):
    @classmethod
    def setUpClass(cls):
        post_save.disconnect(update_finding_aids_index, sender=FindingAidsEntity)
        post_save.disconnect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.disconnect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        post_save.connect(update_finding_aids_index, sender=FindingAidsEntity)
        post_save.connect(update_finding_aids_index_upon_container_save, sender=Container)
        post_save.connect(update_isad_when_archival_unit_saved, sender=ArchivalUnit)

    def setUp(self):
        super().setUp()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.carrier_type = make_carrier_types(type='VHS')
        self.primary_type = make_primary_types(type='Moving Image')
        self.access_rights = make_access_rights()

        self.container = make_container(
            series=self.series,
            carrier_type=self.carrier_type,
            barcode='HU_OSA_99999999',
        )
        self.digital_version = make_digital_version_container(
            container=self.container,
            level='M',
            identifier='HU_OSA_99999999',
            filename='HU_OSA_99999999.avi',
            technical_metadata=get_tech_md()
        )

        self.fa_yes = make_finding_aids(
            container=self.container,
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
            container=self.container,
            access_rights=self.access_rights,
            folder_no=2,
            primary_type=self.primary_type,
            title='Non-online folder',
            date_from='2020-01-01',
            digital_version_exists=True,
            digital_version_online=False,
        )

    def test_container_list_filters_digital_version_exists(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-list'),
            {'container__barcode': 'HU_OSA_99999999'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        ids = [row['id'] for row in response.data['results']]
        self.assertIn(self.digital_version.id, ids)

    def test_container_detail_returns_metadata_field(self):
        response = self.client.get(
            reverse('digitization-v1:digitization-detail', kwargs={'pk': self.digital_version.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('technical_metadata', response.data)

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
