from datetime import datetime
from dateutil.relativedelta import relativedelta
from rest_framework.response import Response
from rest_framework.views import APIView

from accession.models import Accession
from finding_aids.models import FindingAidsEntity
from isaar.models import Isaar
from isad.models import Isad


class AnalyticsActivityView(APIView):
    """
    Returns monthly creation activity for dashboard analytics.

    The response provides per-month counts for the last three years for:
        - Accessions
        - ISAD(G) records
        - ISAAR records
        - Finding aids entities

    Response format:
        A flat list of objects with:
            - month: "YYYY/MM"
            - type: one of the tracked entity labels
            - value: count created in that month
    """

    def get(self, request):
        """
        Builds a month sequence for the last three years and counts creations per month.

        The month list includes each month boundary starting at the first day
        of the month and ending at the current month.
        """
        date_from = datetime.now() - relativedelta(years=3)
        date_to = datetime.now()

        total_months = lambda dt: dt.month + 12 * dt.year
        month_list = []
        for tot_m in range(total_months(date_from) - 1, total_months(date_to)):
            y, m = divmod(tot_m, 12)
            month_list.append(datetime(y, m + 1, 1))

        analytics_data = []
        for month in month_list:

            # Accessions
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'Accession',
                'value': Accession.objects.filter(date_created__year=month.year, date_created__month=month.month).count()
            })

            # ISAD
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'ISAD(G)',
                'value': Isad.objects.filter(date_created__year=month.year, date_created__month=month.month).count()
            })

            # ISAAR
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'ISAAR',
                'value': Isaar.objects.filter(date_created__year=month.year, date_created__month=month.month).count()
            })

            # Finding Aids
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'Finding Aids',
                'value': FindingAidsEntity.objects.filter(date_created__year=month.year, date_created__month=month.month).count()
            })

        return Response(analytics_data)


class AnalyticsTotalView(APIView):
    """
    Returns cumulative totals for dashboard analytics.

    The response provides per-month cumulative counts (<= month boundary)
    for the last three years for:
        - Accessions
        - ISAD(G) records
        - ISAAR records
        - Finding aids entities

    Response format:
        A flat list of objects with:
            - month: "YYYY/MM"
            - type: one of the tracked entity labels
            - value: cumulative count up to that month
    """

    def get(self, request):
        """
        Builds a month sequence for the last three years and counts cumulative totals.

        Cumulative values are computed using `date_created__lte=month`, where
        `month` is the first day of the month.
        """
        date_from = datetime.now() - relativedelta(years=3)
        date_to = datetime.now()

        total_months = lambda dt: dt.month + 12 * dt.year
        month_list = []
        for tot_m in range(total_months(date_from) - 1, total_months(date_to)):
            y, m = divmod(tot_m, 12)
            month_list.append(datetime(y, m + 1, 1))

        analytics_data = []
        for month in month_list:

            # Accessions
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'Accession',
                'value': Accession.objects.filter(date_created__lte=month).count()
            })

            # ISAD
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'ISAD(G)',
                'value': Isad.objects.filter(date_created__lte=month).count()
            })

            # ISAAR
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'ISAAR',
                'value': Isaar.objects.filter(date_created__lte=month).count()
            })

            # Finding Aids
            analytics_data.append({
                'month': month.strftime("%Y/%m"),
                'type': 'Finding Aids',
                'value': FindingAidsEntity.objects.filter(date_created__lte=month).count()
            })

        return Response(analytics_data)