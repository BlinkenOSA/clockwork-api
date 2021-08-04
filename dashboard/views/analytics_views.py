from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from rest_framework.response import Response
from rest_framework.views import APIView

from accession.models import Accession
from finding_aids.models import FindingAidsEntity
from isaar.models import Isaar
from isad.models import Isad


class AnalyticsActivityView(APIView):
    def get(self, request):
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
    def get(self, request):
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