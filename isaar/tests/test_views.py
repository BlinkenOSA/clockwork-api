from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from isaar.models import Isaar, IsaarRelationship, IsaarPlaceQualifier


class IsaarViewsTest(TestViewsBaseClass):
    def setUp(self):
        self.init()
        self.isaar_a = Isaar.objects.create(
            name='Alpha Org',
            type='C',
            date_existence_from='1990-01-01',
            date_existence_to='2000-01-01',
            status='Draft',
        )
        self.isaar_b = Isaar.objects.create(
            name='Beta Person',
            type='P',
            date_existence_from='1980-01-01',
            date_existence_to='1990-01-01',
            status='Final',
        )
        IsaarRelationship.objects.create(relationship='Earlier name')
        IsaarPlaceQualifier.objects.create(id=1, qualifier='Headquarters')

    def test_list_filter_by_type(self):
        response = self.client.get(reverse('isaar-v1:isaar-list'), {'type': 'C'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['name'], 'Alpha Org')

    def test_select_search_by_name(self):
        response = self.client.get(reverse('isaar-v1:isaar-select-list'), {'search': 'Beta'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['name'], 'Beta Person')

    def test_create_sets_user_created(self):
        payload = {
            'name': 'Gamma Entity',
            'type': 'C',
            'date_existence_from': '2001-01-01',
            'date_existence_to': '2010-01-01',
        }
        response = self.client.post(reverse('isaar-v1:isaar-list'), data=payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['user_created'], self.user.username)

    def test_relationship_select_list(self):
        response = self.client.get(reverse('isaar-v1:isaar-select-relationship'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['relationship'], 'Earlier name')

    def test_place_qualifier_select_list(self):
        response = self.client.get(reverse('isaar-v1:isaar-select-place-qualifier'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['qualifier'], 'Headquarters')
