# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2017-11-06 18:45
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0125_auto_20171107_1643'),
    ]

    operations = [
        migrations.AddField(
            model_name='flowrun',
            name='path',
            field=models.TextField(help_text='The path taken during this flow run in JSON format', null=True),
        ),
    ]
