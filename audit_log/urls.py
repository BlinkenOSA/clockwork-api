from django.urls import re_path, path

from audit_log.views import AuditLogList

app_name = 'audit_log'

urlpatterns = [
    path('', AuditLogList.as_view(), name='audit-log-list'),
]
