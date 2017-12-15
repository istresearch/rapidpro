# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-12-15 09:06
from __future__ import unicode_literals

import json

from django.conf import settings
from django.db import migrations

from temba.orgs.models import Org, NEXMO_KEY, NEXMO_SECRET, NEXMO_APP_ID, NEXMO_APP_PRIVATE_KEY


class Migration(migrations.Migration):

    dependencies = [
        ('channels', '0081_update-nexmo-callback-url-channel-config'),
    ]

    def update_nexmo_bulk_sender_channels_config(apps, schema_editor):
        Channel = apps.get_model('channels', 'Channel')

        if settings.IS_PROD:
            nexmo_channels = Channel.objects.filter(channel_type='NX', is_active=True)
            for channel in nexmo_channels:
                try:
                    org = Org.objects.get(pk=channel.org_id)
                    org_config = org.config_json()
                    app_id = org_config[NEXMO_APP_ID]
                    config = {'nexmo_app_id': app_id,
                              'nexmo_app_private_key': org_config[NEXMO_APP_PRIVATE_KEY],
                              'nexmo_api_key': org_config[NEXMO_KEY],
                              'nexmo_api_secret': org_config[NEXMO_SECRET]}

                    channel.config = json.dumps(config)
                    channel.tps = 1
                    channel.save(update_fields=['config', 'tps'])
                except Exception as e:
                    import traceback
                    traceback.print_exc(e)
                    pass

    operations = [
        migrations.RunPython(update_nexmo_bulk_sender_channels_config)
    ]
