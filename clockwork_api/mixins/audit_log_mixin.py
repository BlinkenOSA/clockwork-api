import re
from audit_log.models import AuditLog


class AuditLogMixin(object):
    def perform_create(self, serializer):
        user = self.request.user
        instance = serializer.save()
        self.log_audit_action(user=user, action='CREATE', instance=instance)
        return instance

    def perform_update(self, serializer):
        changed_fields = []
        changed_m2m_fields = []
        changed_o2m_fields = []

        user = self.request.user

        old_instance = self.get_object()

        # Before save event
        old_m2m_values = {}
        m2m_fields = self.get_related_fields(old_instance, 'm2m')
        # Check m2m fields - old instance
        for field in m2m_fields:
            old_m2m_values[field] = [value.id for value in getattr(old_instance, field).all()]

        old_o2m_values = {}
        o2m_fields = self.get_related_fields(old_instance, 'o2m')
        # Check o2m fields - old instance
        for field in o2m_fields:
            old_o2m_values[field] = [record for record in getattr(old_instance, field).values().all()]

        # Save new records
        instance = serializer.save()

        # Check m2m fields - new instance
        for field in m2m_fields:
            if old_m2m_values.get(field, []) != [value.id for value in getattr(instance, field).all()]:
                changed_m2m_fields.append(field)

        # Check m2o fields - new instance
        for field in o2m_fields:
            if old_o2m_values.get(field, []) != [record for record in getattr(instance, field).values().all()]:
                instance_model_name = instance._meta.object_name
                o2m_model_name = getattr(instance, field).model._meta.object_name
                field_name = o2m_model_name.replace(instance_model_name, '')

                # Create the proper field name, similar to the regular field names
                pattern = re.compile(r'(?<!^)(?=[A-Z])')
                fn = pattern.sub('_', field_name).lower()

                changed_o2m_fields.append(fn)

        changed_fields += self.compare_objects(old_instance=old_instance, new_instance=instance)
        changed_fields += changed_m2m_fields
        changed_fields += changed_o2m_fields

        if changed_fields:
            # Log only if there are actually changes
            self.log_audit_action(user=user, action='UPDATE', instance=instance, changed_fields=changed_fields)

        return instance

    def perform_destroy(self, instance):
        user = self.request.user
        self.log_audit_action(user=user, action='DELETE', instance=instance)
        return instance

    @staticmethod
    def get_related_fields(instance, type):
        field_list = instance._meta.get_fields()
        fields = []

        if type == 'm2m':
            for field in field_list:
                if field.many_to_many:
                    fields.append(field.name)

        if type == 'o2m':
            for field in field_list:
                if field.one_to_many:
                    if field.related_name:
                        fields.append(field.related_name)
                    else:
                        fields.append("%s_set" % field.name)

        return fields

    @staticmethod
    def compare_objects(old_instance, new_instance):
        # Identify the fields that have changed
        changed_fields = []

        fields_to_skip = [
            'user_created', 'user_updated', 'user_published'
            'date_created', 'date_updated', 'date_published'
        ]

        for field in new_instance._meta.fields:
            field_name = field.name
            if field_name not in fields_to_skip:
                old_value = getattr(old_instance, field_name)
                new_value = getattr(new_instance, field_name)

                old_value = None if old_value == "" else old_value
                new_value = None if new_value == "" else new_value

                if old_value != new_value:
                    changed_fields.append(field_name)

        return changed_fields

    @staticmethod
    def log_audit_action(user=None, action=None, instance=None, changed_fields=None):
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            changed_fields=changed_fields,  # Save only changed fields here
        )
