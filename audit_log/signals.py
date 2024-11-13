from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver
from .models import AuditLog
from django.contrib.auth import get_user_model
from .utils import log_audit_action
import json


@receiver(pre_save)
def log_update_or_create(sender, instance, **kwargs):
    if sender == AuditLog:
        return  # Ignore logging changes for the AuditLog model itself

    if instance.pk:
        # The instance already exists, so this is an update
        old_instance = sender.objects.get(pk=instance.pk)

        # Identify the fields that have changed
        changed_fields = []
        old_data = {}
        new_data = {}

        for field in instance._meta.fields:
            field_name = field.name
            old_value = getattr(old_instance, field_name)
            new_value = getattr(instance, field_name)

            if old_value != new_value:
                changed_fields.append(field_name)
                old_data[field_name] = old_value
                new_data[field_name] = new_value

        if changed_fields:
            # Log only if there are actually changes
            log_audit_action(
                user=None,  # User will be set in log_audit_action using get_current_user()
                action='UPDATE',
                instance=instance,
                changed_fields=changed_fields,
                old_data=old_data,
                new_data=new_data
            )
    else:
        # This is a new instance, so it’s a creation
        new_data = {field.name: getattr(instance, field.name) for field in instance._meta.fields}
        log_audit_action(
            user=None,
            action='CREATE',
            instance=instance,
            new_data=new_data
        )


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    # Ignore the AuditLog model itself to avoid recursive logging
    if sender == AuditLog:
        return

    old_data = json.loads(instance.to_json())
    log_audit_action(user=None, action='DELETE', instance=instance, old_data=old_data)