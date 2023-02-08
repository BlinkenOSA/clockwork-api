# Generated by Django 4.1.3 on 2023-02-08 15:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('controlled_list', '0006_nationality'),
        ('research', '0019_alter_requestitem_status'),
    ]

    operations = [
        migrations.AlterField(
            model_name='researcher',
            name='citizenship',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='controlled_list.nationality'),
        ),
    ]
