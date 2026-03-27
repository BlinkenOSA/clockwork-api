from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types


class ContainerViewsTest(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.carrier_type = make_carrier_types()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.container = make_container(self.series, self.carrier_type)

    def test_precreate_returns_next_container_no(self):
        response = self.client.get(
            reverse('container-v1:container-pre-create', kwargs={'pk': self.series.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['archival_unit'], self.series.id)
        self.assertEqual(response.data['container_no'], 2)

    def test_list_respects_allowed_archival_units(self):
        other_subfonds = make_subfonds(
            fonds=300,
            subfonds=2,
            level='SF',
            title='Other Subfonds',
            parent=self.fonds
        )
        other_series = make_series(
            fonds=300,
            subfonds=2,
            series=1,
            level='S',
            title='Other Series',
            parent=other_subfonds
        )
        make_container(
            series=other_series,
            carrier_type=self.carrier_type,
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
