from datetime import timedelta

from django.utils import timezone
from rest_framework import status
from rest_framework.reverse import reverse

from clockwork_api.tests.test_views_base_class import TestViewsBaseClass
from research.models import Researcher, ResearcherVisit


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
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': self.old_researcher.date_created.strftime('%Y-%m'), 'total': 3},
            ]
        )

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
        self.old_researcher.date_created = timezone.datetime(2026, 1, 15, tzinfo=timezone.utc)
        self.old_researcher.save(update_fields=['date_created'])

        self.mid_researcher.date_created = timezone.datetime(2026, 3, 10, tzinfo=timezone.utc)
        self.mid_researcher.save(update_fields=['date_created'])

        self.new_researcher.date_created = timezone.datetime(2026, 3, 20, tzinfo=timezone.utc)
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
        self.assertEqual(
            response.data['by_month'],
            [
                {'month': self.old_visit.check_in.strftime('%Y-%m'), 'total': 3},
            ]
        )

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
        self.old_visit.check_in = timezone.datetime(2026, 1, 15, 9, 0, tzinfo=timezone.utc)
        self.old_visit.check_out = timezone.datetime(2026, 1, 15, 12, 0, tzinfo=timezone.utc)
        self.old_visit.save(update_fields=['check_in', 'check_out'])

        self.mid_visit.check_in = timezone.datetime(2026, 3, 10, 10, 0, tzinfo=timezone.utc)
        self.mid_visit.check_out = timezone.datetime(2026, 3, 10, 12, 0, tzinfo=timezone.utc)
        self.mid_visit.save(update_fields=['check_in', 'check_out'])

        self.open_visit.check_in = timezone.datetime(2026, 3, 20, 9, 0, tzinfo=timezone.utc)
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
