from rest_framework.reverse import reverse

from accession.tests.helpers import make_accession
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from django.utils import timezone
from django_date_extensions.fields import ApproximateDate

from accession.models import Accession, AccessionMethod
from donor.models import Donor


class AccessionViewTest(TestViewsBaseClass):
    """ Testing Accession endpoints """
    @classmethod
    def setUpTestData(cls):
        cls.accession = make_accession()

    def test_filter_class(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'search': 'test'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_year(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'transfer_year': '1995'})
        self.assertEqual(response.data['count'], 1)

    def test_filter_year_not_exists(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'transfer_year': '1996'})
        self.assertEqual(response.data['count'], 0)

    def test_filter_fonds(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': '206'})
        self.assertEqual(response.data['count'], 1)

    def test_fonds_not_exists(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': '301'})
        self.assertEqual(response.data['count'], 0)

    def test_fonds_not_a_number(self):
        response = self.client.get(reverse('accession-v1:accession-list'), {'fonds': 'abc'})
        self.assertEqual(response.data['count'], 0)

    def test_precreate_seq_increments_for_current_year(self):
        response = self.client.get(reverse('accession-v1:accession-pre-create'))
        self.assertEqual(response.status_code, 200)
        year = timezone.now().year
        self.assertEqual(response.data['seq'], f"{year}/002")
