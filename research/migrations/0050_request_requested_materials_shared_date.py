from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0049_requestitem_other_identifier'),
    ]

    operations = [
        migrations.AddField(
            model_name='request',
            name='requested_materials_shared_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
