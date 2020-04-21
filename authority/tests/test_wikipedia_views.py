from rest_framework import status
from rest_framework.reverse import reverse
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class WikipediaTest(TestViewsBaseClass):
    """ Testing Wikipedia endpoint """

    def setUp(self):
        self.init()

    def test_get_query(self):
        response = self.client.get(reverse('authority-v1:wikipedia-list'), {'query': 'Lenin'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        has_result = len(list(filter(lambda r: r['url'] == "http://en.wikipedia.org/wiki/Vladimir Lenin", response.data))) == 1
        self.assertTrue(has_result)
