from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authority', '0009_alter_person_simhash64'),
    ]

    operations = [
        migrations.AddField(
            model_name='corporation',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='corporation',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='country',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='country',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='genre',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='genre',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='language',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='person',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='place',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='wikidata_cache',
            field=models.JSONField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='wikidata_cache_updated_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
