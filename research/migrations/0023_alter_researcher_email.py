# Generated by Django 4.1.3 on 2023-02-08 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0022_alter_researcher_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='email',
            field=models.EmailField(blank=True, max_length=100, null=True, unique=True),
        ),
    ]
