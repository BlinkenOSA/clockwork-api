from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from authority.models import Language
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from isad.models import Isad


class IsadExtraViewsTests(TestViewsBaseClass):
    def setUp(self):
        self.init()
        self.fonds = ArchivalUnit.objects.create(fonds=1001, level='F', title='Fonds')
        self.subfonds = ArchivalUnit.objects.create(
            fonds=1001,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=self.fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1001,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=self.subfonds,
        )
        self.language = Language.objects.create(language='English')

    def test_precreate_endpoint(self):
        response = self.client.get(reverse('isad-v1:isad-pre-create', kwargs={'pk': self.fonds.id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['archival_unit'], self.fonds.id)
        self.assertEqual(response.data['description_level'], 'F')

    def test_create_sets_user_created(self):
        payload = {
            'archival_unit': self.fonds.id,
            'title': self.fonds.title,
            'reference_code': self.fonds.reference_code,
            'description_level': 'F',
            'year_from': 1995,
            'language': [self.language.id],
        }
        response = self.client.post(reverse('isad-v1:isad-create'), data=payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_created'], self.user.username)

    def test_select_list_filter_and_search(self):
        isad_fonds = Isad.objects.create(
            archival_unit=self.fonds,
            description_level='F',
            year_from=1990,
        )
        isad_fonds.language.add(self.language)

        isad_series = Isad.objects.create(
            archival_unit=self.series,
            description_level='S',
            year_from=2000,
        )
        isad_series.language.add(self.language)

        response = self.client.get(
            reverse('isad-v1:isad-select-list'),
            {'archival_unit__series': self.series.series},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], isad_series.id)

        response = self.client.get(reverse('isad-v1:isad-select-list'), {'search': 'Fonds'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], isad_fonds.id)

    def test_index_test_view_catalog_target(self):
        with patch('isad.views.isad_index_views.ISADNewCatalogIndexer') as indexer_cls:
            indexer = indexer_cls.return_value
            indexer.isad = object()
            indexer.get_solr_document.return_value = {'id': 'doc-1'}

            response = self.client.get(
                reverse('isad-v1:isad-isad-test-view', kwargs={'target': 'catalog', 'pk': 1})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {'id': 'doc-1'})
        indexer.create_solr_document.assert_called_once()

    def test_index_test_view_not_found(self):
        with patch('isad.views.isad_index_views.ISADAMSIndexer') as indexer_cls:
            indexer = indexer_cls.return_value
            indexer.isad = None

            response = self.client.get(
                reverse('isad-v1:isad-isad-test-view', kwargs={'target': 'ams', 'pk': 1})
            )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
