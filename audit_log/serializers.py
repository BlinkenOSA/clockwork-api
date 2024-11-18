from rest_framework import serializers

from audit_log.models import AuditLog


class AuditLogReadSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = AuditLog
        fields = '__all__'