from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('archival_unit', '0004_alter_archivalunit_fonds_and_more'),
        ('accounts', '0002_alter_userprofile_allowed_archival_units_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='allowed_unprocessed_series',
            field=models.ManyToManyField(
                blank=True,
                help_text='Leave empty to allow access to every series in the unprocessed-materials fonds.',
                related_name='unprocessed_materials_users',
                to='archival_unit.archivalunit',
                verbose_name='allowed unprocessed series',
            ),
        ),
    ]
