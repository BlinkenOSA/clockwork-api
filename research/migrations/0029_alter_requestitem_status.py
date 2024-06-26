# Generated by Django 4.1.7 on 2023-06-06 12:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0028_researcher_how_do_you_know_osa_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestitem',
            name='status',
            field=models.CharField(choices=[('1', 'In Queue'), ('2', 'Pending'), ('3', 'Processed and prepared'), ('4', 'Returned'), ('5', 'Reshelved'), ('9', 'Uploaded')], default='3', max_length=1),
        ),
    ]
