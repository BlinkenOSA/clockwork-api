import datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.reverse import reverse

from archival_unit.models import ArchivalUnit
from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from container.models import Container
from controlled_list.models import AccessRight, CarrierType, PrimaryType
from finding_aids.models import FindingAidsEntity
from research.models import Researcher, Request, RequestItem, RequestItemPart


class RequestSubmissionDateTests(TestViewsBaseClass):
    fixtures = ['carrier_types', 'primary_types', 'access_rights']

    def setUp(self):
        super().setUp()
        researcher = Researcher.objects.create(
            first_name='Ada', last_name='Lovelace', email='ada@example.com', status='approved',
        )
        fonds = ArchivalUnit.objects.create(fonds=1201, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1201, subfonds=1, level='SF', title='Subfonds', parent=fonds,
        )
        series = ArchivalUnit.objects.create(
            fonds=1201, subfonds=1, series=1, level='S', title='Series', parent=subfonds,
        )
        container = Container.objects.create(
            archival_unit=series, carrier_type=CarrierType.objects.first(),
            digital_version_exists=True, barcode='HU_OSA_SUBMITTED',
        )
        entity = FindingAidsEntity.objects.create(
            archival_unit=series, container=container, folder_no=1, title='Restricted folder',
            date_from='2020-01-01', primary_type=PrimaryType.objects.first(),
            access_rights=AccessRight.objects.get(statement='Restricted'),
        )
        self.items = []
        self.parts = []
        self.created_dates = []
        now = timezone.now()
        # Insert the newest submission first; planned visits run in the opposite order.
        for index in range(2):
            request = Request.objects.create(
                researcher=researcher, request_date=now + datetime.timedelta(days=index + 1),
            )
            created_date = now - datetime.timedelta(minutes=index)
            Request.objects.filter(pk=request.pk).update(created_date=created_date)
            item = RequestItem.objects.create(request=request, item_origin='FA', container=container)
            part = RequestItemPart.objects.create(request_item=item, finding_aids_entity=entity)
            self.items.append(item.id)
            self.parts.append(part.id)
            self.created_dates.append(created_date)

    def assert_submission_order(self, endpoint, ordering_field, ids):
        for direction, expected_ids in (('', list(reversed(ids))), ('-', ids)):
            with self.subTest(endpoint=endpoint, direction=direction):
                response = self.client.get(reverse(endpoint), {'ordering': direction + ordering_field})
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                results = response.json()['results']
                self.assertEqual([row['id'] for row in results], expected_ids)
                for row in results:
                    expected_date = self.created_dates[ids.index(row['id'])]
                    self.assertEqual(parse_datetime(row['created_date']), expected_date)

    def test_regular_and_digital_lists_expose_and_sort_submission_dates(self):
        for endpoint in ('research-v1:requests-list', 'research-v1:requests-digital-list'):
            self.assert_submission_order(endpoint, 'request__created_date', self.items)

    def test_restricted_list_exposes_and_sorts_parent_submission_dates(self):
        self.assert_submission_order(
            'research-v1:restricted-requests-list', 'request_item__request__created_date', self.parts,
        )
