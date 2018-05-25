# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-05-24 18:26
from __future__ import unicode_literals

from django.db import migrations


SQL = """
CREATE INDEX CONCURRENTLY IF NOT EXISTS msgs_msg_org_id_created_on_id_idx on msgs_msg(org_id, created_on, id)
"""


class Migration(migrations.Migration):
    atomic = False

    dependencies = [("msgs", "0117_msg_uuid_index")]

    operations = [migrations.RunSQL(SQL)]
