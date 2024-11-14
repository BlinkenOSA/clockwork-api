from django.db.models.signals import pre_save, post_save, pre_delete
from django.dispatch import receiver

from accession.models import Accession
from archival_unit.models import ArchivalUnit
from container.models import Container
from donor.models import Donor
from finding_aids.models import FindingAidsEntity
from isaar.models import Isaar
from isad.models import Isad
from .models import AuditLog
from django.contrib.auth import get_user_model
from .utils import log_audit_action
import json


@receiver(pre_save)
def log_update_or_create(sender, instance, **kwargs):
    tracked_models = [
        Accession, ArchivalUnit, Container, Donor, FindingAidsEntity, Isaar, Isad
    ]

    fields_to_skip = [
        'user_created', 'user_updated', 'user_published'
        'date_created', 'date_updated', 'date_published'
    ]

    if sender not in tracked_models or sender == AuditLog:
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
            if field_name not in fields_to_skip:
                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)

                old_value = None if old_value == "" else old_value
                new_value = None if new_value == "" else new_value

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
            )
    else:
        # This is a new instance, so it’s a creation
        log_audit_action(
            user=None,
            action='CREATE',
            instance=instance
        )


@receiver(pre_delete)
def log_delete(sender, instance, **kwargs):
    # Ignore the AuditLog model itself to avoid recursive logging
    if sender == AuditLog:
        return
    log_audit_action(user=None, action='DELETE', instance=instance)