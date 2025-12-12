"""
URL configuration for the `audit_log` app.

This module exposes a single endpoint that provides read-only access to
audit trail entries. The view supports filtering by object ID, model name,
and action type.
"""
from django.urls import path

from audit_log.views import AuditLogList

app_name = 'audit_log'

urlpatterns = [
    path('', AuditLogList.as_view(), name='audit-log-list'),
]
