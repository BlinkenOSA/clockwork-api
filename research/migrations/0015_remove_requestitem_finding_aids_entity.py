# Generated by Django 4.1.3 on 2023-01-24 12:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0014_requestitem_container'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestitem',
            name='finding_aids_entity',
        ),
    ]
