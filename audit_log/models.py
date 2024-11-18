from django.db import models
from django.contrib.auth.models import User


class AuditLog(models.Model):
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

    def __str__(self):
        return f"{self.user} {self.action} {self.model_name} (ID: {self.object_id})"
