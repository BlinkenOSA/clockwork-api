from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0047_requestedmaterialssharepointjob'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='served_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
