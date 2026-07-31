from unittest.mock import patch

from django.contrib.auth.models import Group
from django.test import override_settings
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.no_index_signals_mixin import NoIndexSignalsMixin
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType
from digitization.models import DigitalVersion
from isad.models import Isad


@override_settings(CATALOG_URL='https://catalog.example')
class DigitalObjectUpsertViewTests(NoIndexSignalsMixin, TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        api_group = Group.objects.create(name='Api')
        self.user.groups.add(api_group)

        self.fonds = ArchivalUnit.objects.create(fonds=306, level='F', title='Fonds')
        self.subfonds = ArchivalUnit.objects.create(
            fonds=306,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=self.fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=306,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=self.subfonds,
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
            barcode='HU_OSA_306_1_1_0001',
            digital_version_exists=False,
        )

    @patch('workflow.views.digital_object_upsert_views.index_catalog_finding_aids_entity.delay')
    def test_access_rc_upsert_sets_default_research_cloud_path(self, mocked_delay):
        response = self.client.post(
            reverse(
                'workflow-v1:digital_object_access_copy_upsert_rc',
                kwargs={'file_name': 'HU_OSA_306_1_1_0001.pdf'}
            ),
            data={},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        digital_version = DigitalVersion.objects.get(pk=response.data['digital_version_id'])
        self.assertEqual(
            digital_version.research_cloud_path,
            'HU OSA 306/HU OSA 306-1/HU OSA 306-1-1/HU_OSA_306_1_1_0001.pdf'
        )
        mocked_delay.assert_not_called()

    @patch('workflow.views.digital_object_upsert_views.index_catalog_finding_aids_entity.delay')
    def test_access_rc_upsert_inserts_optional_subdirectory_into_research_cloud_path(self, mocked_delay):
        response = self.client.post(
            reverse(
                'workflow-v1:digital_object_access_copy_upsert_rc',
                kwargs={'file_name': 'HU_OSA_306_1_1_0001.pdf'}
            ),
            data={'subdirectory': 'access-copies'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        digital_version = DigitalVersion.objects.get(pk=response.data['digital_version_id'])
        self.assertEqual(
            digital_version.research_cloud_path,
            'HU OSA 306/HU OSA 306-1/HU OSA 306-1-1/access-copies/HU_OSA_306_1_1_0001.pdf'
        )
        mocked_delay.assert_not_called()
