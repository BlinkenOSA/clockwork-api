# Generated by Django 4.1.10 on 2024-06-19 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0019_alter_findingaidsentity_physical_condition'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='catalog_id',
            field=models.CharField(blank=True, db_index=True, max_length=12, null=True),
        )
    ]