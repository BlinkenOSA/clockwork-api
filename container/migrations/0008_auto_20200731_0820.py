# Generated by Django 2.2.12 on 2020-07-31 08:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0007_auto_20190704_1226'),
    ]

    operations = [
        migrations.AlterField(
            model_name='container',
            name='container_no',
            field=models.IntegerField(),
        ),
    ]
