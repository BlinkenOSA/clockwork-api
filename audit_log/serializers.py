from rest_framework import serializers

from audit_log.models import AuditLog


class AuditLogReadSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for audit log entries.

    This serializer is typically used when displaying audit history
    in administrative interfaces or object-level logs. It exposes all
    model fields, replacing the `user` relation with the username for
    convenience.

    Fields:
        user (str):
            Rendered as a username instead of a nested user object.
    """
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = AuditLog
        fields = '__all__'