# Generated by Django 4.1.7 on 2023-03-10 13:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0008_auto_20200731_0820'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='digital_version_research_cloud',
            field=models.BooleanField(default=False),
        ),
    ]