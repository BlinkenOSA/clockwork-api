from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
    """
    Stores an audit trail entry for changes made in the system.

    Each record represents a single action performed by a user on a model
    instance (e.g. CREATE, UPDATE, DELETE, CLONE). Optionally, a snapshot
    of changed fields can be stored to support later inspection or debugging.

    Attributes:
        id (int):
            Primary key for the audit log entry.

        user (User | None):
            The user who performed the action. May be null if the action
            cannot be associated with a user (e.g. system tasks).

        action (str):
            The type of action performed. One of:
                - "CREATE"
                - "UPDATE"
                - "DELETE"
                - "CLONE"

        model_name (str):
            The name of the model on which the action was performed.
            Typically stored as "<ModelName>".

        object_id (int | None):
            The primary key of the affected object, if applicable.

        timestamp (datetime):
            The date and time when the action was logged.

        changed_fields (dict | list | None):
            Optional JSON-serializable structure describing what changed.
            A list of changed field names.
    """
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('CLONE', 'Create (Clone)'),
    ]

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, db_index=True)
    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)
    model_name = models.CharField(max_length=100, db_index=True)
    object_id = models.PositiveIntegerField(blank=True, null=True, db_index=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    changed_fields = models.JSONField(null=True, blank=True)  # Add this field

    class Meta:
        db_table = 'audit_logs'
        ordering = ["-timestamp"]

    def __str__(self):
        """
        Returns a concise human-readable representation of the audit entry.

        Example:
            "alice UPDATE ArchivalUnit (ID: 42)"
        """
        return f"{self.user} {self.action} {self.model_name} (ID: {self.object_id})"
