# Generated by Django 4.1.10 on 2024-11-18 07:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('audit_log', '0003_alter_auditlog_action_alter_auditlog_changed_fields_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='auditlog',
            name='timestamp',
            field=models.DateTimeField(auto_now_add=True),
        ),
    ]
