# Generated by Django 4.1.7 on 2023-04-14 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0012_alter_findingaidsentitydate_date_to'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='digital_version_exists',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='digital_version_online',
            field=models.BooleanField(db_index=True, default=False),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='digital_version_research_cloud',
            field=models.BooleanField(db_index=True, default=False),
        ),
    ]
