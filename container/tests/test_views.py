from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.tests.helpers import make_fonds, make_subfonds, make_series
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from container.tests.helpers import make_container
from controlled_list.tests.helpers import make_carrier_types, make_access_rights, make_primary_types
from finding_aids.tests.helpers import make_finding_aids


class ContainerViewsTest(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        self.carrier_type = make_carrier_types()
        self.fonds = make_fonds()
        self.subfonds = make_subfonds(self.fonds)
        self.series = make_series(self.subfonds)
        self.container = make_container(self.series, self.carrier_type)
        self.access_rights = make_access_rights()
        self.primary_type = make_primary_types()

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

    def test_move_container_between_series_and_renumber(self):
        source_second = make_container(self.series, self.carrier_type)
        source_third = make_container(self.series, self.carrier_type)
        destination_series = make_series(
            self.subfonds,
            series=2,
            uuid='930cd383-505f-456c-b60c-e12447efc08e',
            title='Destination series',
        )
        destination_first = make_container(destination_series, self.carrier_type)
        destination_second = make_container(destination_series, self.carrier_type)

        response = self.client.post(
            reverse('container-v1:container-move'),
            data={
                'container': source_second.id,
                'source_series': self.series.id,
                'destination_series': destination_series.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], source_second.id)
        self.assertEqual(response.data['archival_unit'], destination_series.id)
        self.assertEqual(response.data['container_no'], 3)
        self.assertEqual(
            list(Container.objects.filter(archival_unit=self.series).order_by('container_no').values_list(
                'id', 'container_no'
            )),
            [(self.container.id, 1), (source_third.id, 2)],
        )
        self.assertEqual(
            list(Container.objects.filter(archival_unit=destination_series).order_by('container_no').values_list(
                'id', 'container_no'
            )),
            [
                (destination_first.id, 1),
                (destination_second.id, 2),
                (source_second.id, 3),
            ],
        )

    def test_move_rejects_container_from_another_source_series(self):
        destination_series = make_series(
            self.subfonds,
            series=2,
            uuid='b54b4307-96ab-45dd-854d-6dfa22987a1f',
            title='Destination series',
        )
        make_container(destination_series, self.carrier_type)

        response = self.client.post(
            reverse('container-v1:container-move'),
            data={
                'container': self.container.id,
                'source_series': destination_series.id,
                'destination_series': self.series.id,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('container', response.data)

    @patch('finding_aids.signals.index_meilisearch_finding_aids_entity_remove.delay')
    @patch('finding_aids.signals.index_catalog_finding_aids_entity_remove.delay')
    @patch('finding_aids.signals.index_meilisearch_finding_aids_entity.delay')
    @patch('finding_aids.signals.index_catalog_finding_aids_entity.delay')
    def test_container_publish_triggers_indexing_signals(
            self,
            mock_catalog_index,
            mock_meili_index,
            mock_catalog_remove,
            mock_meili_remove,
    ):
        finding_aids = make_finding_aids(
            container=self.container,
            primary_type=self.primary_type,
            access_rights=self.access_rights,
            published=False
        )
        # Creating a FindingAidsEntity can trigger multiple saves/signals
        # (catalog_id generation path). We only assert the publish endpoint effect.
        mock_catalog_index.reset_mock()
        mock_meili_index.reset_mock()
        mock_catalog_remove.reset_mock()
        mock_meili_remove.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.put(
                reverse('container-v1:container-publish', kwargs={'action': 'publish', 'pk': self.container.id})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        finding_aids.refresh_from_db()
        self.assertTrue(finding_aids.published)
        self.assertEqual(mock_catalog_index.call_count, 1)
        self.assertEqual(mock_meili_index.call_count, 1)

    @patch('finding_aids.signals.index_meilisearch_finding_aids_entity_remove.delay')
    @patch('finding_aids.signals.index_catalog_finding_aids_entity_remove.delay')
    @patch('finding_aids.signals.index_meilisearch_finding_aids_entity.delay')
    @patch('finding_aids.signals.index_catalog_finding_aids_entity.delay')
    def test_container_unpublish_triggers_indexing_signals(
            self,
            mock_catalog_index,
            mock_meili_index,
            mock_catalog_remove,
            mock_meili_remove,
    ):
        finding_aids = make_finding_aids(
            container=self.container,
            primary_type=self.primary_type,
            access_rights=self.access_rights,
            published=True
        )
        # Creating a FindingAidsEntity can trigger multiple saves/signals
        # (catalog_id generation path). We only assert the unpublish endpoint effect.
        mock_catalog_index.reset_mock()
        mock_catalog_remove.reset_mock()
        mock_meili_index.reset_mock()
        mock_meili_remove.reset_mock()

        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.put(
                reverse('container-v1:container-publish', kwargs={'action': 'unpublish', 'pk': self.container.id})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        finding_aids.refresh_from_db()
        self.assertFalse(finding_aids.published)
        self.assertEqual(mock_catalog_remove.call_count, 1)
        self.assertEqual(mock_meili_index.call_count, 1)
