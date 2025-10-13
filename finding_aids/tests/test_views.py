import json

from rest_framework import status
from rest_framework.reverse import reverse
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class FindingAidsPublishTest(TestViewsBaseClass):
    """ Testing Finding Aids publishing endpoints"""
    fixtures = ['carrier_types', 'primary_types', 'access_rights', 'archival_unit_themes', 'finding_aids']

    def setUp(self):
        self.init()
        self.user.save()
        self.container_id = 5675
        self.series_id = 908

    def test_fa_create(self):
        finding_aids = {
            'folder_no': 3,
            'title': 'Test Folder',
            'date_from': '1990-01-01',
        }
        response = self.client.post(
            reverse('finding_aids-v1:finding_aids-create', kwargs={'container_id': self.container_id}),
            data=finding_aids
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED,
                         msg=f"Failed with {response.status_code}. Response:\n{json.dumps(response.json(), indent=2)}")
        self.assertEqual(response.data['title'], finding_aids['title'])
        self.assertEqual(response.data['container'], self.container_id)
        self.assertEqual(response.data['archival_unit'], self.series_id)

    def test_publish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': '174492'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': '174492'}))
        self.assertEqual(response.data['published'], True)
        self.assertEqual(response.data['user_published'], self.user.username)

    def test_unpublish(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'unpublish', 'pk': '174491'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(reverse('finding_aids-v1:finding_aids-detail',
                                           kwargs={'pk': '174491'}))
        self.assertEqual(response.data['published'], False)
        self.assertEqual(response.data['user_published'], "")

    def test_publish_non_existent(self):
        response = self.client.put(reverse('finding_aids-v1:finding_aids-publish',
                                           kwargs={'action': 'publish', 'pk': 999}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_select_by_container(self):
        response = self.client.get(reverse('finding_aids-v1:finding_aids-select', kwargs={'container_id': '5675'}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
