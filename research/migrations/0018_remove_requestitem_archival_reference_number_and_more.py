# Generated by Django 4.1.3 on 2023-02-02 08:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0017_requestitem_return_date_alter_requestitem_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requestitem',
            name='archival_reference_number',
        ),
        migrations.RemoveField(
            model_name='requestitem',
            name='archival_unit',
        ),
    ]
