# Generated by Django 4.1.7 on 2023-06-07 08:52

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controlled_list', '0006_nationality'),
        ('finding_aids', '0014_findingaidsentity_access_rights_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='access_rights',
            field=models.ForeignKey(blank=True, default=1, null=True, on_delete=django.db.models.deletion.PROTECT, to='controlled_list.accessright'),
        ),
    ]
