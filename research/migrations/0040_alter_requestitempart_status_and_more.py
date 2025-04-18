# Generated by Django 4.1.10 on 2025-03-21 11:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0039_rename_approved_by_requestitempart_decision_by_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestitempart',
            name='status',
            field=models.CharField(choices=[('1', 'In Queue'), ('2', 'Pending'), ('3', 'Processed and prepared'), ('4', 'Returned'), ('5', 'Reshelved'), ('9', 'Uploaded')], db_index=True, default='new', max_length=20),
        ),
        migrations.AlterField(
            model_name='requestitemrestriction',
            name='request_item',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='restriction', to='research.requestitem'),
        ),
    ]
