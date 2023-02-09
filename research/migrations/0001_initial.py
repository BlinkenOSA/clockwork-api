# Generated by Django 4.1.3 on 2022-12-05 14:56

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Request',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('request_date', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'research_request',
            },
        ),
        migrations.CreateModel(
            name='Researcher',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('card_number', models.IntegerField()),
                ('token', models.CharField(max_length=200)),
                ('first_name', models.CharField(max_length=100)),
                ('last_name', models.CharField(max_length=100)),
                ('middle_name', models.CharField(blank=True, max_length=100, null=True)),
                ('address_hungary', models.CharField(blank=True, max_length=200, null=True)),
                ('address_abroad', models.CharField(blank=True, max_length=200, null=True)),
                ('city_hungary', models.CharField(blank=True, max_length=100, null=True)),
                ('city_abroad', models.CharField(blank=True, max_length=100, null=True)),
                ('country', models.CharField(blank=True, max_length=100, null=True)),
                ('id_number', models.CharField(max_length=50)),
                ('email', models.EmailField(max_length=100)),
                ('citizenship', models.CharField(max_length=100)),
                ('is_student', models.BooleanField(default=True)),
                ('is_staff', models.BooleanField(default=False)),
                ('research_subject', models.TextField()),
                ('research_will_be_published', models.BooleanField(default=False)),
                ('date_is_tentative', models.BooleanField(default=False)),
                ('active', models.BooleanField(default=False)),
                ('approved', models.BooleanField(default=False)),
            ],
            options={
                'db_table': 'research_researcher',
                'unique_together': {('email', 'card_number')},
            },
        ),
        migrations.CreateModel(
            name='RequestItems',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('item_origin', models.CharField(choices=[('FA', 'Finding Aids'), ('L', 'Library'), ('FL', 'Film Library')], max_length=3)),
                ('archival_reference_number', models.CharField(max_length=30)),
                ('identifier', models.CharField(max_length=20)),
                ('title', models.CharField(blank=True, max_length=200, null=True)),
                ('request_date', models.DateTimeField(auto_now_add=True)),
                ('closing_date', models.DateTimeField(blank=True, null=True)),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='research.request')),
            ],
            options={
                'db_table': 'research_request_items',
            },
        ),
        migrations.AddField(
            model_name='request',
            name='researcher',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='research.researcher'),
        ),
    ]