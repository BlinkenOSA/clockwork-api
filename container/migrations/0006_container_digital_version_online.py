from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('container', '0005_auto_20180918_0730'),
    ]

    operations = [
        migrations.AddField(
            model_name='container',
            name='digital_version_online',
            field=models.BooleanField(default=False),
        ),
    ]