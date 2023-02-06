# Generated by Django 4.1.3 on 2023-01-16 11:55

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('research', '0007_rename_occpuation_type_researcher_occupation_type'),
    ]

    operations = [
        migrations.RenameField(
            model_name='requestitems',
            old_name='closing_date',
            new_name='reshelve_date',
        ),
        migrations.RemoveField(
            model_name='requestitems',
            name='request_date',
        ),
        migrations.AddField(
            model_name='request',
            name='finishing_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='request',
            name='processed_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='request',
            name='status',
            field=models.CharField(default='N', max_length=1),
        ),
        migrations.AlterModelTable(
            name='request',
            table='research_requests',
        ),
        migrations.AlterModelTable(
            name='researcher',
            table='research_researchers',
        ),
        migrations.AlterModelTable(
            name='researcherdegree',
            table='research_researcher_degrees',
        ),
        migrations.CreateModel(
            name='ResearcherVisit',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('check_in', models.DateTimeField(auto_now_add=True)),
                ('check_out', models.DateTimeField(blank=True, null=True)),
                ('researcher', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='research.researcher')),
            ],
            options={
                'db_table': 'research_researcher_visits',
            },
        ),
    ]
