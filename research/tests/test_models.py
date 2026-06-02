import datetime

from django.test import TestCase

from archival_unit.models import ArchivalUnit
from container.models import Container
from controlled_list.models import CarrierType
from research.models import Researcher, Request, RequestItem


class ResearchModelsTests(TestCase):
    fixtures = ['carrier_types']

    def test_researcher_card_number_and_name(self):
        r1 = Researcher.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com')
        r2 = Researcher.objects.create(first_name='Alan', last_name='Turing', email='alan@example.com')

        self.assertEqual(r1.card_number, 1)
        self.assertEqual(r2.card_number, 2)
        self.assertEqual(r1.name, 'Lovelace, Ada')

    def test_request_item_queue_promotion_and_return_date(self):
        researcher = Researcher.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com')
        request = Request.objects.create(researcher=researcher, request_date=datetime.datetime.now())

        pending = RequestItem.objects.create(request=request, item_origin='L', status='2')
        queued = RequestItem.objects.create(request=request, item_origin='L', status='1')

        pending.status = '4'
        pending.save()

        queued.refresh_from_db()
        pending.refresh_from_db()

        self.assertEqual(queued.status, '2')
        self.assertIsNotNone(pending.return_date)

    def test_request_item_ordering_for_finding_aids(self):
        researcher = Researcher.objects.create(first_name='Ada', last_name='Lovelace', email='ada@example.com')
        request = Request.objects.create(researcher=researcher, request_date=datetime.datetime.now())

        fonds = ArchivalUnit.objects.create(fonds=1200, level='F', title='Fonds')
        subfonds = ArchivalUnit.objects.create(
            fonds=1200,
            subfonds=1,
            level='SF',
            title='Subfonds',
            parent=fonds,
        )
        series = ArchivalUnit.objects.create(
            fonds=1200,
            subfonds=1,
            series=1,
            level='S',
            title='Series',
            parent=subfonds,
        )
        container = Container.objects.create(archival_unit=series, carrier_type=CarrierType.objects.first())

        item = RequestItem.objects.create(request=request, item_origin='FA', container=container)
        self.assertEqual(item.ordering, f"{series.sort}0001")
