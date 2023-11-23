# Generated by Django 4.1.10 on 2023-11-23 10:44

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0017_alter_findingaidsentity_date_created_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4),
        ),
    ]
