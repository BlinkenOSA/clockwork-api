# Generated by Django 4.1.7 on 2023-03-29 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0010_findingaidsentity_digital_version_research_cloud_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='archival_reference_code',
            field=models.CharField(blank=True, db_index=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='legacy_id',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True),
        ),
    ]