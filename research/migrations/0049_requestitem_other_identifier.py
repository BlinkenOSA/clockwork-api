from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0048_requestitem_served_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='other_identifier',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
