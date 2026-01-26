import re

from audit_log.models import AuditLog


class AuditLogMixin:
    """
    Mixin for automatic audit logging of create, update, and delete operations.

    This mixin tracks changes made through Django REST Framework views and
    records them in the AuditLog table.

    Supported operations:
        - CREATE → Logged after successful creation
        - UPDATE → Logged only if actual field changes occurred
        - DELETE → Logged before deletion

    Logged information includes:
        - User performing the action
        - Action type (CREATE, UPDATE, DELETE)
        - Model name
        - Object ID
        - Changed fields (for updates)

    Features:
        - Detects changes in regular model fields
        - Tracks many-to-many relationships
        - Tracks one-to-many related objects
        - Avoids logging unchanged updates

    Intended use:
        Mixed into DRF generic views (CreateAPIView, UpdateAPIView,
        RetrieveUpdateDestroyAPIView, etc.).

    Example:
        class MyView(AuditLogMixin, generics.UpdateAPIView):
            ...
    """

    def perform_create(self, serializer):
        """
        Save a newly created instance and log a CREATE action.

        Args:
            serializer: DRF serializer instance containing validated data.
        """
        user = self.request.user
        instance = serializer.save()

        self.log_audit_action(
            user=user,
            action='CREATE',
            instance=instance
        )

    def perform_update(self, serializer):
        """
        Save an updated instance and log an UPDATE action if changes occurred.

        Compares the original and updated instances to detect:
            - Modified model fields
            - Changed many-to-many relationships
            - Changed one-to-many related objects

        Only logs the update if at least one field has changed.

        Args:
            serializer: DRF serializer instance containing validated data.
        """
        changed_fields = []
        changed_m2m_fields = []
        changed_o2m_fields = []

        user = self.request.user

        # Store original instance for comparison
        old_instance = self.get_object()

        # Capture original many-to-many values
        old_m2m_values = {}
        m2m_fields = self.get_related_fields(old_instance, 'm2m')

        for field in m2m_fields:
            if hasattr(old_instance, field):
                old_m2m_values[field] = [
                    value.id for value in getattr(old_instance, field).all()
                ]

        # Capture original one-to-many values
        old_o2m_values = {}
        o2m_fields = self.get_related_fields(old_instance, 'o2m')

        for field in o2m_fields:
            if hasattr(old_instance, field):
                old_o2m_values[field] = [
                    record for record in getattr(old_instance, field).values().all()
                ]

        # Save updated instance
        instance = serializer.save()

        # Detect many-to-many changes
        for field in m2m_fields:
            if hasattr(instance, field):
                if old_m2m_values.get(field, []) != [
                    value.id for value in getattr(instance, field).all()
                ]:
                    changed_m2m_fields.append(field)

        # Detect one-to-many changes
        for field in o2m_fields:
            if hasattr(instance, field):
                if old_o2m_values.get(field, []) != [
                    record for record in getattr(instance, field).values().all()
                ]:
                    instance_model_name = instance._meta.object_name
                    o2m_model_name = getattr(instance, field).model._meta.object_name
                    field_name = o2m_model_name.replace(instance_model_name, '')

                    # Convert CamelCase to snake_case
                    pattern = re.compile(r'(?<!^)(?=[A-Z])')
                    fn = pattern.sub('_', field_name).lower()

                    changed_o2m_fields.append(fn)

        # Detect standard field changes
        changed_fields += self.compare_objects(
            old_instance=old_instance,
            new_instance=instance
        )

        changed_fields += changed_m2m_fields
        changed_fields += changed_o2m_fields

        # Log only if changes exist
        if changed_fields:
            self.log_audit_action(
                user=user,
                action='UPDATE',
                instance=instance,
                changed_fields=changed_fields
            )

    def perform_destroy(self, instance):
        """
        Log a DELETE action and remove the instance.

        Args:
            instance: Model instance being deleted.
        """
        user = self.request.user

        self.log_audit_action(
            user=user,
            action='DELETE',
            instance=instance
        )

        instance.delete()

    @staticmethod
    def get_related_fields(instance, type):
        """
        Retrieve related field names for the given instance.

        Args:
            instance: Django model instance.
            type (str): Relationship type ('m2m' or 'o2m').

        Returns:
            list[str]: List of related field names.
        """
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
                        fields.append(f"{field.name}_set")

        return fields

    @staticmethod
    def compare_objects(old_instance, new_instance):
        """
        Compare two model instances and detect changed fields.

        Ignores system-maintained metadata fields.

        Args:
            old_instance: Original model instance.
            new_instance: Updated model instance.

        Returns:
            list[str]: Names of fields that changed.
        """
        changed_fields = []

        fields_to_skip = [
            'user_created', 'user_updated', 'user_published',
            'date_created', 'date_updated', 'date_published'
        ]

        for field in new_instance._meta.fields:
            field_name = field.name

            if field_name not in fields_to_skip:
                old_value = getattr(old_instance, field_name)
                new_value = getattr(new_instance, field_name)

                # Normalize empty strings
                old_value = None if old_value == "" else old_value
                new_value = None if new_value == "" else new_value

                if old_value != new_value:
                    changed_fields.append(field_name)

        return changed_fields

    @staticmethod
    def log_audit_action(user=None, action=None, instance=None, changed_fields=None):
        """
        Persist an audit log entry.

        Args:
            user: User performing the action.
            action (str): Action type (CREATE, UPDATE, DELETE).
            instance: Affected model instance.
            changed_fields (list[str], optional): Fields modified during update.
        """
        AuditLog.objects.create(
            user=user,
            action=action,
            model_name=instance.__class__.__name__,
            object_id=instance.pk,
            changed_fields=changed_fields,
        )
