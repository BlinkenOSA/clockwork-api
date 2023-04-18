# Generated by Django 4.1.7 on 2023-04-18 12:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0024_alter_researcher_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='researcher',
            name='occupation_other',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AddField(
            model_name='researcher',
            name='occupation_type_other',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='researcher',
            name='occupation_type',
            field=models.CharField(blank=True, choices=[('student', 'Student'), ('staff', 'Staff'), ('faculty', 'Faculty'), ('other', 'Other')], max_length=20, null=True),
        ),
    ]
