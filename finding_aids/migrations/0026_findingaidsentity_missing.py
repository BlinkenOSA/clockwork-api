from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0025_findingaidsentity_ark'),
    ]

    operations = [
        migrations.AddField(
            model_name='findingaidsentity',
            name='missing',
            field=models.BooleanField(default=False),
        ),
    ]
