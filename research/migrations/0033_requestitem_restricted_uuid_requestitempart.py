# Generated by Django 4.1.10 on 2024-01-29 12:13

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('finding_aids', '0019_alter_findingaidsentity_physical_condition'),
        ('research', '0032_rename_hcaptcha_researcher_captcha'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestitem',
            name='restricted_uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4),
        ),
        migrations.CreateModel(
            name='RequestItemPart',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('finding_aids_entity', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='finding_aids.findingaidsentity')),
                ('request_item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='research.requestitem')),
            ],
            options={
                'db_table': 'research_request_items_parts',
            },
        ),
    ]