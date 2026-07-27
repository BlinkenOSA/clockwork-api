from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0046_researcher_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestedMaterialsSharePointJob',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('completed', 'Completed'), ('failed', 'Failed')], db_index=True, default='pending', max_length=20)),
                ('current_step', models.CharField(choices=[('queued', 'Queued'), ('checking_files', 'Checking files'), ('creating_directory', 'Creating directory'), ('copying_files', 'Copying files'), ('sharing_directory', 'Sharing directory'), ('sending_emails', 'Sending emails'), ('completed', 'Completed'), ('failed', 'Failed')], default='queued', max_length=30)),
                ('message', models.TextField(blank=True, null=True)),
                ('progress_current', models.IntegerField(default=0)),
                ('progress_total', models.IntegerField(default=5)),
                ('celery_task_id', models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                ('result', models.JSONField(blank=True, null=True)),
                ('error_message', models.TextField(blank=True, null=True)),
                ('created_date', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('started_date', models.DateTimeField(blank=True, null=True)),
                ('finished_date', models.DateTimeField(blank=True, null=True)),
                ('request', models.ForeignKey(on_delete=models.deletion.CASCADE, related_name='requested_materials_jobs', to='research.request')),
            ],
            options={
                'db_table': 'research_requested_materials_sharepoint_jobs',
            },
        ),
    ]
