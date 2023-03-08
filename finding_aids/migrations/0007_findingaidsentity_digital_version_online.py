from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0005_auto_20201019_0901'),
    ]

    operations = [
        migrations.AddField(
            model_name='findingaidsentity',
            name='digital_version_online',
            field=models.BooleanField(default=False),
        ),
    ]