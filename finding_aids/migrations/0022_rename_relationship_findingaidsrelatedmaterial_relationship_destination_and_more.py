# Generated by Django 4.1.10 on 2024-10-24 11:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0021_findingaidsrelatedmaterial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='findingaidsrelatedmaterial',
            old_name='relationship',
            new_name='relationship_destination',
        ),
        migrations.AddField(
            model_name='findingaidsrelatedmaterial',
            name='relationship_source',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
    ]