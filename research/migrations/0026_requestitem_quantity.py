# Generated by Django 4.1.7 on 2023-05-04 13:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0025_researcher_occupation_other_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='quantity',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
