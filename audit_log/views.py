from rest_framework import generics
from audit_log.models import AuditLog
from audit_log.serializers import AuditLogReadSerializer
from django_filters.rest_framework import DjangoFilterBackend


class AuditLogList(generics.ListAPIView):
    queryset = AuditLog.objects.filter()
    serializer_class = AuditLogReadSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_fields = ['object_id', 'action', 'model_name']
    pagination_class = None
