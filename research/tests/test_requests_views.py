import datetime
from unittest.mock import patch

from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import CarrierType
from research.models import Researcher, Request, RequestItem
from research.views.requests_views import RequestLibraryMLR


class ResearchRequestsViewsTests(TestViewsBaseClass):
    fixtures = ['carrier_types']

    def setUp(self):
        self.init()
        self.researcher = Researcher.objects.create(
            first_name='Ada',
            last_name='Lovelace',
            email='ada@example.com',
            status='approved',
        )
        self.request = Request.objects.create(researcher=self.researcher, request_date=datetime.datetime.now())

        fonds = ArchivalUnit.objects.create(fonds=1201, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1201,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        self.series = ArchivalUnit.objects.create(
            fonds=1201,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        self.container = Container.objects.create(
            archival_unit=self.series,
            carrier_type=CarrierType.objects.first(),
            digital_version_exists=True,
            barcode='HU_OSA_REQ',
        )

    def test_request_item_status_step_next_with_digital_version(self):
        item = RequestItem.objects.create(
            request=self.request,
            item_origin='FA',
            container=self.container,
            status='2',
        )

        with patch('research.views.requests_views.EmailWithTemplate.send_request_delivered_user') as send_mail:
            response = self.client.put(
                reverse('research-v1:request-item-status-change', kwargs={'action': 'next', 'request_item_id': item.id})
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, '9')
        send_mail.assert_called_once()

    def test_request_item_status_step_previous(self):
        item = RequestItem.objects.create(
            request=self.request,
            item_origin='L',
            status='4',
        )

        response = self.client.put(
            reverse('research-v1:request-item-status-change', kwargs={'action': 'previous', 'request_item_id': item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item.refresh_from_db()
        self.assertEqual(item.status, '3')

    def test_requests_list_for_print_only_pending(self):
        RequestItem.objects.create(request=self.request, item_origin='L', status='2')
        RequestItem.objects.create(request=self.request, item_origin='L', status='5')

        response = self.client.get(reverse('research-v1:requests-list-for-print'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['status'], '2')


class RequestLibraryMLRHelperTests(TestViewsBaseClass):
    def setUp(self):
        self.init()
        self.view = RequestLibraryMLR()

    def test_get_locations_defaults_to_general_collection(self):
        items = [{'952': {'subfields': [{'a': 'x'}]}}]
        locations = self.view._get_locations(items)
        self.assertEqual(locations, {'General collection'})

    def test_get_collections_extracts_subfield_a(self):
        fields = [{'580': {'subfields': [{'a': 'Collection A'}, {'b': 'ignored'}]}}]
        collections = self.view._get_collections(fields)
        self.assertEqual(collections, {'Collection A'})
