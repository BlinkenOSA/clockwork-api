# Generated by Django 4.1.3 on 2023-01-23 08:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0008_rename_closing_date_requestitems_reshelve_date_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='request',
            name='finishing_date',
        ),
        migrations.RemoveField(
            model_name='request',
            name='processed_date',
        ),
        migrations.RemoveField(
            model_name='request',
            name='status',
        ),
        migrations.AddField(
            model_name='request',
            name='created_date',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='requestitems',
            name='status',
            field=models.CharField(default='N', max_length=1),
        ),
        migrations.AlterField(
            model_name='request',
            name='request_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
