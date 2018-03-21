# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-21 16:20
from __future__ import unicode_literals

from django.db import migrations
import temba.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0147_new_engine_changes'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowrun',
            name='events',
            field=temba.utils.models.JSONAsTextField(default=list, help_text='The events recorded on this run in JSON format', null=True),
        ),
    ]
