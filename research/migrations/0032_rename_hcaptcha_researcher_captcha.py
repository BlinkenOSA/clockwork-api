# Generated by Django 4.1.10 on 2023-11-21 16:18

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0031_researcher_hcaptcha'),
    ]

    operations = [
        migrations.RenameField(
            model_name='researcher',
            old_name='hcaptcha',
            new_name='captcha',
        ),
    ]
