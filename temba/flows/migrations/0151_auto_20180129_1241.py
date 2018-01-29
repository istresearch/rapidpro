# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-01-29 12:41
from __future__ import unicode_literals

from django.db import migrations
import temba.utils.models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0150_auto_20180129_1137'),
    ]

    operations = [
        migrations.AlterField(
            model_name='actionset',
            name='actions',
            field=temba.utils.models.JSONAsTextField(help_text='The JSON encoded actions for this action set'),
        ),
    ]
