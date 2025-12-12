from rest_framework import generics
from audit_log.models import AuditLog
from audit_log.serializers import AuditLogReadSerializer
from django_filters.rest_framework import DjangoFilterBackend


class AuditLogList(generics.ListAPIView):
    """
    Returns a list of audit log entries.

    This endpoint provides:
       - Filtering by ``object_id``, ``action``, and ``model_name``
       - Unpaginated output (suitable for history screens)
       - Read-only access using ``AuditLogReadSerializer``

    Typical usage:
       - Viewing the full audit history of a model instance
       - Displaying activity logs in admin dashboards
       - Filtering logs for a specific model type or action type

    Query Parameters:
       object_id (int):
           Filters logs for a specific related object ID.
       action (str):
           One of: CREATE, UPDATE, DELETE, CLONE.
       model_name (str):
           Model name such as "archival_unit.ArchivalUnit".
    """
    queryset = AuditLog.objects.filter()
    serializer_class = AuditLogReadSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['object_id', 'action', 'model_name']
    pagination_class = None
