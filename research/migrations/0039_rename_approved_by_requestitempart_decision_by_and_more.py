# Generated by Django 4.1.10 on 2025-01-08 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0038_remove_requestitemrestriction_approved_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requestitempart',
            old_name='approved_by',
            new_name='decision_by',
        ),
        migrations.RenameField(
            model_name='requestitempart',
            old_name='approved_date',
            new_name='decision_date',
        ),
        migrations.RemoveField(
            model_name='requestitempart',
            name='approved',
        ),
        migrations.AddField(
            model_name='requestitempart',
            name='status',
            field=models.CharField(choices=[('1', 'In Queue'), ('2', 'Pending'), ('3', 'Processed and prepared'), ('4', 'Returned'), ('5', 'Reshelved'), ('9', 'Uploaded')], db_index=True, default='new', max_length=8),
        ),
    ]
