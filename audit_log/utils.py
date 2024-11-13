from .models import AuditLog
from .middleware import get_current_user


def log_audit_action(user=None, action=None, instance=None, changed_fields=None, old_data=None, new_data=None):
    if user is None:
        user = get_current_user()
    AuditLog.objects.create(
        user=user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=instance.pk,
        changed_fields=changed_fields,  # Save only changed fields here
    )