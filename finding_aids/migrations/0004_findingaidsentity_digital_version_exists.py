from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0003_auto_20181206_1416'),
    ]

    operations = [
        migrations.AddField(
            model_name='findingaidsentity',
            name='digital_version_exists',
            field=models.BooleanField(default=False),
        ),
    ]