from datetime import timedelta
from collections import Counter

from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from controlled_list.models import CarrierType
from research.models import Researcher, ResearcherVisit, Request, RequestItem
from archival_unit.models import ArchivalUnit
from container.models import Container


class ResearcherRegistrationStatisticsViewsTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        now = timezone.now()

        self.old_researcher = Researcher.objects.create(
            first_name='Old',
            last_name='Researcher',
            email='old@example.com',
            occupation='ceu',
        )
        self.old_researcher.date_created = now - timedelta(days=10)
        self.old_researcher.save(update_fields=['date_created'])

        self.mid_researcher = Researcher.objects.create(
            first_name='Mid',
            last_name='Researcher',
            email='mid@example.com',
            occupation='other',
        )
        self.mid_researcher.date_created = now - timedelta(days=5)
        self.mid_researcher.save(update_fields=['date_created'])

        self.new_researcher = Researcher.objects.create(
            first_name='New',
            last_name='Researcher',
            email='new@example.com',
            occupation='other',
        )
        self.new_researcher.date_created = now - timedelta(days=1)
        self.new_researcher.save(update_fields=['date_created'])

    def test_returns_total_and_grouped_by_occupation(self):
        response = self.client.get(reverse('research-v1:researcher-registration-statistics'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 3)
        self.assertEqual(
            response.data['by_occupation'],
            [
                {'occupation': 'ceu', 'total': 1},
                {'occupation': 'other', 'total': 2},
            ]
        )
        expected_month_totals = Counter(
            researcher.date_created.strftime('%Y-%m')
            for researcher in (
                self.old_researcher,
                self.mid_researcher,
                self.new_researcher,
            )
        )
        for month, total in expected_month_totals.items():
            self.assertIn({'month': month, 'total': total}, response.data['by_month'])

    def test_filters_by_date_interval(self):
        response = self.client.get(
            reverse('research-v1:researcher-registration-statistics'),
            {
                'date_from': (timezone.now() - timedelta(days=6)).date().isoformat(),
                'date_to': (timezone.now() - timedelta(days=2)).date().isoformat(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 1)
        self.assertEqual(
            response.data['by_occupation'],
            [
                {'occupation': 'other', 'total': 1},
            ]
        )
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': self.mid_researcher.date_created.strftime('%Y-%m'), 'total': 1},
            ]
        )

    def test_returns_monthly_totals_for_each_month_in_requested_range(self):
        self.old_researcher.date_created = timezone.datetime(2026, 1, 15)
        self.old_researcher.save(update_fields=['date_created'])

        self.mid_researcher.date_created = timezone.datetime(2026, 3, 10)
        self.mid_researcher.save(update_fields=['date_created'])

        self.new_researcher.date_created = timezone.datetime(2026, 3, 20)
        self.new_researcher.save(update_fields=['date_created'])

        response = self.client.get(
            reverse('research-v1:researcher-registration-statistics'),
            {
                'date_from': '2026-01-01',
                'date_to': '2026-03-31',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': '2026-01', 'total': 1},
                {'month': '2026-02', 'total': 0},
                {'month': '2026-03', 'total': 2},
            ]
        )

    def test_returns_bad_request_for_invalid_date_range(self):
        response = self.client.get(
            reverse('research-v1:researcher-registration-statistics'),
            {
                'date_from': '2026-04-10',
                'date_to': '2026-04-01',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'date_from cannot be later than date_to.')


class ResearcherVisitStatisticsViewsTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        now = timezone.now()

        self.researcher = Researcher.objects.create(
            first_name='Visit',
            last_name='Researcher',
            email='visit@example.com',
            occupation='ceu',
        )

        self.old_visit = ResearcherVisit.objects.create(researcher=self.researcher)
        self.old_visit.check_in = now - timedelta(days=10, hours=4)
        self.old_visit.check_out = now - timedelta(days=10, hours=1)
        self.old_visit.save(update_fields=['check_in', 'check_out'])

        self.mid_visit = ResearcherVisit.objects.create(researcher=self.researcher)
        self.mid_visit.check_in = now - timedelta(days=5, hours=5)
        self.mid_visit.check_out = now - timedelta(days=5, hours=3)
        self.mid_visit.save(update_fields=['check_in', 'check_out'])

        self.open_visit = ResearcherVisit.objects.create(researcher=self.researcher)
        self.open_visit.check_in = now - timedelta(days=1, hours=2)
        self.open_visit.check_out = None
        self.open_visit.save(update_fields=['check_in', 'check_out'])

    def test_returns_total_visits_and_total_hours(self):
        response = self.client.get(reverse('research-v1:researcher-visit-statistics'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_visits'], 3)
        self.assertEqual(response.data['total_hours'], 5.0)
        expected_month_totals = Counter(
            visit.check_in.strftime('%Y-%m')
            for visit in (
                self.old_visit,
                self.mid_visit,
                self.open_visit,
            )
        )
        for month, total in expected_month_totals.items():
            self.assertIn({'month': month, 'total': total}, response.data['by_month'])

    def test_filters_visits_by_date_interval(self):
        response = self.client.get(
            reverse('research-v1:researcher-visit-statistics'),
            {
                'date_from': (timezone.now() - timedelta(days=6)).date().isoformat(),
                'date_to': (timezone.now() - timedelta(days=2)).date().isoformat(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_visits'], 1)
        self.assertEqual(response.data['total_hours'], 2.0)
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': self.mid_visit.check_in.strftime('%Y-%m'), 'total': 1},
            ]
        )

    def test_returns_monthly_visit_totals_for_each_month_in_requested_range(self):
        self.old_visit.check_in = timezone.datetime(2026, 1, 15, 9, 0)
        self.old_visit.check_out = timezone.datetime(2026, 1, 15, 12, 0)
        self.old_visit.save(update_fields=['check_in', 'check_out'])

        self.mid_visit.check_in = timezone.datetime(2026, 3, 10, 10, 0)
        self.mid_visit.check_out = timezone.datetime(2026, 3, 10, 12, 0)
        self.mid_visit.save(update_fields=['check_in', 'check_out'])

        self.open_visit.check_in = timezone.datetime(2026, 3, 20, 9, 0)
        self.open_visit.save(update_fields=['check_in'])

        response = self.client.get(
            reverse('research-v1:researcher-visit-statistics'),
            {
                'date_from': '2026-01-01',
                'date_to': '2026-03-31',
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': '2026-01', 'total': 1},
                {'month': '2026-02', 'total': 0},
                {'month': '2026-03', 'total': 2},
            ]
        )

    def test_returns_bad_request_for_invalid_visit_date_from(self):
        response = self.client.get(
            reverse('research-v1:researcher-visit-statistics'),
            {'date_from': 'invalid-date'}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid date_from. Use YYYY-MM-DD format.')


class RequestedMaterialsStatisticsViewsTests(TestViewsBaseClass):
    def setUp(self):
        super().setUp()
        now = timezone.now()

        self.researcher = Researcher.objects.create(
            first_name='Request',
            last_name='Researcher',
            email='requester@example.com',
            occupation='ceu',
        )

        self.request_old = Request.objects.create(researcher=self.researcher)
        self.request_old.created_date = now - timedelta(days=10)
        self.request_old.save(update_fields=['created_date'])

        self.request_mid = Request.objects.create(researcher=self.researcher)
        self.request_mid.created_date = now - timedelta(days=5)
        self.request_mid.save(update_fields=['created_date'])

        self.request_new = Request.objects.create(researcher=self.researcher)
        self.request_new.created_date = now - timedelta(days=1)
        self.request_new.save(update_fields=['created_date'])

        self.archival_unit = ArchivalUnit.objects.create(fonds=1301, level='F', title='Test Fonds')
        self.second_archival_unit = ArchivalUnit.objects.create(fonds=1302, level='F', title='Second Fonds')
        self.archival_box = CarrierType.objects.create(type='Archival Box', width=10)
        self.vhs_tape = CarrierType.objects.create(type='VHS Tape', width=2)

        self.archival_box_container = Container.objects.create(
            archival_unit=self.archival_unit,
            carrier_type=self.archival_box,
        )
        self.vhs_container = Container.objects.create(
            archival_unit=self.archival_unit,
            carrier_type=self.vhs_tape,
        )
        self.second_archival_box_container = Container.objects.create(
            archival_unit=self.second_archival_unit,
            carrier_type=self.archival_box,
        )

        RequestItem.objects.create(
            request=self.request_old,
            item_origin='FA',
            container=self.archival_box_container,
        )
        RequestItem.objects.create(
            request=self.request_mid,
            item_origin='L',
        )
        RequestItem.objects.create(
            request=self.request_new,
            item_origin='FL',
            container=self.vhs_container,
        )
        RequestItem.objects.create(
            request=self.request_new,
            item_origin='FA',
            container=self.archival_box_container,
        )
        RequestItem.objects.create(
            request=self.request_new,
            item_origin='FA',
            container=self.second_archival_box_container,
        )

    def test_returns_requested_materials_grouped_by_origin_labels(self):
        response = self.client.get(reverse('research-v1:requested-materials-by-origin-statistics'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 5)
        self.assertEqual(
            response.data['by_item_origin'],
            [
                {'item_origin': 'Finding Aids', 'total': 3},
                {'item_origin': 'Film Library', 'total': 1},
                {'item_origin': 'Library', 'total': 1},
            ]
        )

    def test_filters_requested_materials_by_origin_date_interval(self):
        response = self.client.get(
            reverse('research-v1:requested-materials-by-origin-statistics'),
            {
                'date_from': (timezone.now() - timedelta(days=6)).date().isoformat(),
                'date_to': timezone.now().date().isoformat(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 4)
        self.assertEqual(
            response.data['by_item_origin'],
            [
                {'item_origin': 'Finding Aids', 'total': 2},
                {'item_origin': 'Film Library', 'total': 1},
                {'item_origin': 'Library', 'total': 1},
            ]
        )

    def test_returns_requested_materials_grouped_by_carrier_type(self):
        response = self.client.get(reverse('research-v1:requested-materials-by-carrier-type-statistics'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 5)
        self.assertEqual(
            response.data['by_carrier_type'],
            [
                {'carrier_type': 'Unknown', 'total': 1},
                {'carrier_type': 'Archival Box', 'total': 3},
                {'carrier_type': 'VHS Tape', 'total': 1},
            ]
        )

    def test_filters_requested_materials_by_carrier_type_date_interval(self):
        response = self.client.get(
            reverse('research-v1:requested-materials-by-carrier-type-statistics'),
            {
                'date_from': (timezone.now() - timedelta(days=6)).date().isoformat(),
                'date_to': timezone.now().date().isoformat(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 4)
        self.assertEqual(
            response.data['by_carrier_type'],
            [
                {'carrier_type': 'Unknown', 'total': 1},
                {'carrier_type': 'Archival Box', 'total': 2},
                {'carrier_type': 'VHS Tape', 'total': 1},
            ]
        )

    def test_returns_top_requested_archival_units(self):
        response = self.client.get(reverse('research-v1:most-requested-archival-units-statistics'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 4)
        self.assertEqual(
            response.data['archival_units'],
            [
                {
                    'id': self.archival_unit.id,
                    'reference_code': self.archival_unit.reference_code,
                    'title': self.archival_unit.title_full,
                    'total': 3,
                },
                {
                    'id': self.second_archival_unit.id,
                    'reference_code': self.second_archival_unit.reference_code,
                    'title': self.second_archival_unit.title_full,
                    'total': 1,
                },
            ]
        )

    def test_filters_top_requested_archival_units_by_date_interval(self):
        response = self.client.get(
            reverse('research-v1:most-requested-archival-units-statistics'),
            {
                'date_from': (timezone.now() - timedelta(days=6)).date().isoformat(),
                'date_to': timezone.now().date().isoformat(),
            }
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], 3)
        self.assertEqual(
            response.data['archival_units'],
            [
                {
                    'id': self.archival_unit.id,
                    'reference_code': self.archival_unit.reference_code,
                    'title': self.archival_unit.title_full,
                    'total': 2,
                },
                {
                    'id': self.second_archival_unit.id,
                    'reference_code': self.second_archival_unit.reference_code,
                    'title': self.second_archival_unit.title_full,
                    'total': 1,
                },
            ]
        )
