from django.urls import path

from dashboard.views.analytics_views import AnalyticsActivityView, AnalyticsTotalView
from dashboard.views.log_views import AccessionLog, ArchivalUnitLog, IsadCreateLog, IsadUpdateLog, FindingAidsCreateLog, \
    FindingAidsUpdateLog, DigitizationLog
from dashboard.views.statistics_views import LinearMeterView, PublishedItems, CarrierTypes

app_name = 'mlr'

urlpatterns = [
    path('stats/linear-meter/<int:archival_unit>/', LinearMeterView.as_view(), name='linear-meter'),
    path('stats/folders-items/<int:archival_unit>/', PublishedItems.as_view(), name='folders-items'),
    path('stats/carrier-types/<int:archival_unit>/', CarrierTypes.as_view(), name='carrier-types'),

    path('logs/accessions/', AccessionLog.as_view(), name='accession-log'),
    path('logs/archival_units/', ArchivalUnitLog.as_view(), name='archival-unit-log'),
    path('logs/isad-create/', IsadCreateLog.as_view(), name='isad-create-log'),
    path('logs/isad-update/', IsadUpdateLog.as_view(), name='isad-update-log'),
    path('logs/finding-aids-create/', FindingAidsCreateLog.as_view(), name='finding-aids-create-log'),
    path('logs/finding-aids-update/', FindingAidsUpdateLog.as_view(), name='finding-aids-update-log'),
    path('logs/digitization/', DigitizationLog.as_view(), name='digitization-log'),

    path('analytics/activity/', AnalyticsActivityView.as_view(), name='analytics-activity-view'),
    path('analytics/totals/', AnalyticsTotalView.as_view(), name='analytics-totals-view'),
]

