from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0004_findingaidsentity_digital_version_exists'),
    ]

    operations = [
        migrations.AlterField(
            model_name='findingaidsentity',
            name='internal_note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='language_statement',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='language_statement_original',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='note',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='note_original',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='physical_description',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentity',
            name='physical_description_original',
            field=models.TextField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='findingaidsentitydate',
            name='date_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='controlled_list.DateType'),
        ),
    ]