# Generated by Django 4.1.7 on 2023-06-05 09:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('isad', '0007_alter_isad_published'),
    ]

    operations = [
        migrations.AlterField(
            model_name='isad',
            name='published',
            field=models.BooleanField(default=False),
        ),
        migrations.AddIndex(
            model_name='isad',
            index=models.Index(fields=['published'], name='isad_recrod_publish_739429_idx'),
        ),
        migrations.AddIndex(
            model_name='isad',
            index=models.Index(fields=['archival_unit'], name='isad_recrod_archiva_e8fec9_idx'),
        ),
    ]
