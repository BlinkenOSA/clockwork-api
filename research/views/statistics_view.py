from datetime import date

from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from research.models import Researcher, ResearcherVisit, RequestItem


def get_filtered_queryset_by_date(queryset, field_name, request):
    date_from = request.query_params.get('date_from')
    parsed_date_from = None
    if date_from:
        parsed_date_from = parse_date(date_from)
        if parsed_date_from is None:
            return None, None, None, Response(
                {'detail': 'Invalid date_from. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = queryset.filter(**{f'{field_name}__date__gte': parsed_date_from})

    date_to = request.query_params.get('date_to')
    parsed_date_to = None
    if date_to:
        parsed_date_to = parse_date(date_to)
        if parsed_date_to is None:
            return None, None, None, Response(
                {'detail': 'Invalid date_to. Use YYYY-MM-DD format.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        queryset = queryset.filter(**{f'{field_name}__date__lte': parsed_date_to})

    if parsed_date_from and parsed_date_to and parsed_date_from > parsed_date_to:
        return None, None, None, Response(
            {'detail': 'date_from cannot be later than date_to.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return queryset, parsed_date_from, parsed_date_to, None


def get_month_range(date_from, date_to):
    current = date(date_from.year, date_from.month, 1)
    end = date(date_to.year, date_to.month, 1)

    months = []
    while current <= end:
        months.append(current)
        if current.month == 12:
            current = date(current.year + 1, 1, 1)
        else:
            current = date(current.year, current.month + 1, 1)
    return months


def get_choice_label_mapping(choices):
    return dict(choices)


class ResearcherRegistrationStatisticsViews(APIView):
    """
    Returns researcher registration statistics for an optional date interval.

    Query params:
        - date_from: inclusive lower bound in YYYY-MM-DD format
        - date_to: inclusive upper bound in YYYY-MM-DD format

    Response format:
        {
            "total": 10,
            "by_occupation": [
                {"occupation": "ceu", "total": 4},
                ...
            ]
        }
    """

    def get(self, request, *args, **kwargs):
        queryset, parsed_date_from, parsed_date_to, error_response = get_filtered_queryset_by_date(
            Researcher.objects.all(),
            'date_created',
            request
        )
        if error_response:
            return error_response

        by_occupation = list(
            queryset.values('occupation')
            .annotate(total=Count('id'))
            .order_by('occupation')
        )

        monthly_totals = {
            item['month'].date().replace(day=1): item['total']
            for item in queryset.annotate(month=TruncMonth('date_created'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        }

        if parsed_date_from and parsed_date_to:
            month_dates = get_month_range(parsed_date_from, parsed_date_to)
        else:
            month_dates = sorted(monthly_totals.keys())

        by_month = [
            {
                'month': month_date.strftime('%Y-%m'),
                'total': monthly_totals.get(month_date, 0)
            }
            for month_date in month_dates
        ]

        return Response({
            'total': queryset.count(),
            'by_occupation': by_occupation,
            'by_month': by_month,
        })


class ResearcherVisitStatisticsViews(APIView):
    """
    Returns visit counts and total completed visit hours for an optional date interval.

    Query params:
        - date_from: inclusive lower bound in YYYY-MM-DD format
        - date_to: inclusive upper bound in YYYY-MM-DD format

    Response format:
        {
            "total_visits": 10,
            "total_hours": 25.5,
            "by_month": [
                {"month": "2026-01", "total": 4}
            ]
        }
    """

    def get(self, request, *args, **kwargs):
        queryset, parsed_date_from, parsed_date_to, error_response = get_filtered_queryset_by_date(
            ResearcherVisit.objects.all(),
            'check_in',
            request
        )
        if error_response:
            return error_response

        total_seconds = 0
        for visit in queryset.exclude(check_out__isnull=True):
            total_seconds += (visit.check_out - visit.check_in).total_seconds()

        monthly_totals = {
            item['month'].date().replace(day=1): item['total']
            for item in queryset.annotate(month=TruncMonth('check_in'))
            .values('month')
            .annotate(total=Count('id'))
            .order_by('month')
        }

        if parsed_date_from and parsed_date_to:
            month_dates = get_month_range(parsed_date_from, parsed_date_to)
        else:
            month_dates = sorted(monthly_totals.keys())

        by_month = [
            {
                'month': month_date.strftime('%Y-%m'),
                'total': monthly_totals.get(month_date, 0)
            }
            for month_date in month_dates
        ]

        return Response({
            'total_visits': queryset.count(),
            'total_hours': round(total_seconds / 3600, 2),
            'by_month': by_month,
        })


class RequestedMaterialsByOriginStatisticsViews(APIView):
    """
    Returns requested material totals grouped by request item origin label.

    The optional date filters are applied to ``request.created_date``.
    """

    def get(self, request, *args, **kwargs):
        queryset, _, _, error_response = get_filtered_queryset_by_date(
            RequestItem.objects.all(),
            'request__created_date',
            request
        )
        if error_response:
            return error_response

        origin_labels = get_choice_label_mapping(RequestItem.ORIGIN)
        by_origin = [
            {
                'item_origin': origin_labels.get(item['item_origin'], item['item_origin']),
                'total': item['total']
            }
            for item in queryset.values('item_origin')
            .annotate(total=Count('id'))
            .order_by('item_origin')
        ]

        return Response({
            'total': queryset.count(),
            'by_item_origin': by_origin,
        })


class RequestedMaterialsByCarrierTypeStatisticsViews(APIView):
    """
    Returns requested material totals grouped by the container carrier type.

    The optional date filters are applied to ``request.created_date``.
    """

    def get(self, request, *args, **kwargs):
        queryset, _, _, error_response = get_filtered_queryset_by_date(
            RequestItem.objects.all(),
            'request__created_date',
            request
        )
        if error_response:
            return error_response

        by_carrier_type = [
            {
                'carrier_type': item['container__carrier_type__type'] or 'Unknown',
                'total': item['total']
            }
            for item in queryset.values('container__carrier_type__type')
            .annotate(total=Count('id'))
            .order_by('container__carrier_type__type')
        ]

        return Response({
            'total': queryset.count(),
            'by_carrier_type': by_carrier_type,
        })


class MostRequestedArchivalUnitsStatisticsViews(APIView):
    """
    Returns the top 10 most requested archival units.

    The optional date filters are applied to ``request.created_date``.
    Only request items linked to a container archival unit are included.
    """

    def get(self, request, *args, **kwargs):
        queryset, _, _, error_response = get_filtered_queryset_by_date(
            RequestItem.objects.filter(container__archival_unit__isnull=False),
            'request__created_date',
            request
        )
        if error_response:
            return error_response

        top_archival_units = list(
            queryset.values(
                'container__archival_unit__id',
                'container__archival_unit__reference_code',
                'container__archival_unit__title_full',
            )
            .annotate(total=Count('id'))
            .order_by('-total', 'container__archival_unit__reference_code')[:10]
        )

        return Response({
            'total': queryset.count(),
            'archival_units': [
                {
                    'id': item['container__archival_unit__id'],
                    'reference_code': item['container__archival_unit__reference_code'],
                    'title': item['container__archival_unit__title_full'],
                    'total': item['total'],
                }
                for item in top_archival_units
            ],
        })
