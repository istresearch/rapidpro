# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-12 01:20
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('orgs', '0039_auto_20180202_1234'),
    ]

    operations = [
        migrations.CreateModel(
            name='Archive',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('archive_type', models.CharField(choices=[('msg', 'Message'), ('flowrun', 'Flow Runs'), ('session', 'Session')], help_text='The type of record this is an archive for', max_length=16)),
                ('created_on', models.DateTimeField(default=django.utils.timezone.now, help_text='When this archive was created')),
                ('start_date', models.DateField(help_text='The starting modified_on date for records in this archive (inclusive')),
                ('end_date', models.DateField(help_text='The ending modified_on date for records in this archive (exclusive)')),
                ('record_count', models.IntegerField(default=0, help_text='The number of records in this archive')),
                ('archive_size', models.IntegerField(default=0, help_text='The size of this archive in bytes (after gzipping)')),
                ('archive_hash', models.TextField(help_text='The md5 hash of this archive (after gzipping)')),
                ('archive_url', models.URLField(help_text='The full URL for this archive')),
                ('is_purged', models.BooleanField(default=False, help_text='Whether the records in this archive have been purged from the database')),
                ('build_time', models.IntegerField(help_text='The number of milliseconds it took to build and upload this archive')),
                ('org', models.ForeignKey(db_constraint=False, help_text='The org this archive is for', on_delete=django.db.models.deletion.CASCADE, to='orgs.Org')),
            ],
        ),
    ]
