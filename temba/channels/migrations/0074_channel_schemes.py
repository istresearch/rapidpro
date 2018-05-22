# Generated by Django 1.11.2 on 2017-08-03 16:56

import django.contrib.postgres.fields
from django.db import migrations, models


def populate_schemes(apps, schema_editor):
    Channel = apps.get_model('channels', 'Channel')

    # find all channels which aren't 'tel', update their schemes appropriately
    for chan in Channel.objects.all().exclude(scheme='tel'):
        chan.schemes = [chan.scheme]
        chan.save(update_fields=['schemes'])


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0073_auto_20170623_1056'),
    ]

    operations = [
        migrations.AddField(
            model_name='channel',
            name='schemes',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=8), default=['tel'], help_text='The URN schemes this channel supports', size=None, verbose_name='URN Schemes'),
        ),
        migrations.RunPython(populate_schemes)
    ]
