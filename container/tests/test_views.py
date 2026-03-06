from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType


class ContainerViewsTest(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        self.init()
        self.fonds = ArchivalUnit.objects.create(
            fonds=300,
            level='F',
            title='Test Fonds'
        )
        self.subfonds = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=1,
            level='SF',
            title='Test Subfonds',
            parent=self.fonds
        )
        self.series = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=1,
            series=1,
            level='S',
            title='Test Series',
            parent=self.subfonds
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.get(pk=1),
            container_no=1
        )

    def test_precreate_returns_next_container_no(self):
        response = self.client.get(
            reverse('container-v1:container-pre-create', kwargs={'pk': self.series.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['archival_unit'], self.series.id)
        self.assertEqual(response.data['container_no'], 2)

    def test_list_respects_allowed_archival_units(self):
        other_subfonds = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=2,
            level='SF',
            title='Other Subfonds',
            parent=self.fonds
        )
        other_series = ArchivalUnit.objects.create(
            fonds=300,
            subfonds=2,
            series=1,
            level='S',
            title='Other Series',
            parent=other_subfonds
        )
        Container.objects.create(
            archival_unit=other_series,
            carrier_type=CarrierType.objects.get(pk=1),
            container_no=1
        )
        self.user_profile.allowed_archival_units.add(self.series)

        response = self.client.get(
            reverse('container-v1:container-list', kwargs={'series_id': self.series.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], self.container.id)

        response = self.client.get(
            reverse('container-v1:container-list', kwargs={'series_id': other_series.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
