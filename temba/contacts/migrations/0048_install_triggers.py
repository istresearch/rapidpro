# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-06 23:33
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations
from temba.sql import InstallSQL


class Migration(migrations.Migration):

    dependencies = [
        ('contacts', '0047_reset_2'),
    ]

    operations = [
        InstallSQL('0048_contacts')
    ]
