from rest_framework.reverse import reverse

from authority.tests.helpers import make_country
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass

from donor.tests.helpers import make_donor


class DonorViewTest(TestViewsBaseClass):
    """ Testing Donor endpoints """
    def setUp(self):
        super().setUp()
        self.country = make_country(alpha2='CZ', alpha3='CZE', country='Czech Republic')
        self.donor = make_donor(
            corporation_name="Research Support Scheme",
            first_name="",
            last_name="",
            email='oziris.ceu.hu',
            country=self.country
        )

    def test_filter_class(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support scheme'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_class_not_exists(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'support schema'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_search_by_email(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'oziris.ceu.hu'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_search_by_country(self):
        response = self.client.get(reverse('donor-v1:donor-list'), {'search': 'Czech'})
        self.assertEqual(response.data['count'], 1)

    def test_create_person_donor_sets_name_and_user(self):
        payload = {
            'first_name': 'Jane',
            'middle_name': 'W.',
            'last_name': 'Doe',
            'postal_code': '1051',
            'country': self.country.id,
            'city': 'Budapest',
            'address': 'Arany Janos u. 32.',
            'email': 'jane@example.com'
        }

        response = self.client.post(reverse('donor-v1:donor-list'), data=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Jane W. Doe')
        self.assertEqual(response.data['user_created'], self.user.username)

    def test_create_corporation_donor_sets_name(self):
        payload = {
            'corporation_name': 'Example Foundation',
            'postal_code': '1051',
            'country': self.country.id,
            'city': 'Budapest',
            'address': 'Arany Janos u. 32.',
            'email': 'foundation@example.com'
        }

        response = self.client.post(reverse('donor-v1:donor-list'), data=payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['name'], 'Example Foundation')

    def test_select_list_search(self):
        response = self.client.get(reverse('donor-v1:donor-select-list'), {'search': 'support'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
