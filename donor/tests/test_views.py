from rest_framework.reverse import reverse
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass


class DonorViewTest(TestViewsBaseClass):
    """ Testing Donor endpoints """
    fixtures = ['donor']

    def setUp(self):
        self.init()

    def test_filter_class(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support scheme'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_class_not_exists(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support schema'})
        self.assertEqual(response.data['count'], 0)