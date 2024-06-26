# Generated by Django 4.1.10 on 2023-11-15 07:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('digitization', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='digitalversion',
            name='filename',
            field=models.CharField(blank=True, db_index=True, max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='digitalversion',
            name='level',
            field=models.CharField(choices=[('M', 'Master'), ('A', 'Access Copy')], db_index=True, default='A', max_length=1),
        ),
        migrations.AlterField(
            model_name='digitalversion',
            name='identifier',
            field=models.CharField(blank=True, db_index=True, max_length=100, null=True),
        ),
    ]
