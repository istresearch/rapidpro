# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-06-11 15:42
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [("archives", "0006_auto_20180605_1645")]

    operations = [migrations.RenameField(model_name="archive", old_name="deletion_date", new_name="deleted_on")]
