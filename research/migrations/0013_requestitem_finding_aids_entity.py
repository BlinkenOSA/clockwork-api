# Generated by Django 4.1.3 on 2023-01-24 10:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0005_auto_20201019_0901'),
        ('research', '0012_requestitem_archival_unit_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='finding_aids_entity',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='finding_aids.findingaidsentity'),
        ),
    ]
