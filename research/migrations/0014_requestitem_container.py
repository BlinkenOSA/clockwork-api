# Generated by Django 4.1.3 on 2023-01-24 12:15

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0007_auto_20200731_0820'),
        ('research', '0013_requestitem_finding_aids_entity'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='container',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='container.container'),
        ),
    ]