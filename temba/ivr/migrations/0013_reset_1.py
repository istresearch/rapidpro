# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-06 22:38
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('channels', '0050_reset_1'),
    ]

    operations = [
        migrations.CreateModel(
            name='IVRCall',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('channels.channelsession',),
        ),
    ]
