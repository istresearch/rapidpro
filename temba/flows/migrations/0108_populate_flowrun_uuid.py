# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-06-29 07:18
from __future__ import unicode_literals

from django.db import migrations
from uuid import uuid4


def populate_flowrun_uuid(FlowRun):
    run_ids = list(FlowRun.objects.filter(uuid=None).values_list('id', flat=True))
    if not run_ids:
        return

    print("Fetched %d flow run ids that need UUIDs..." % len(run_ids))
    num_updated = 0

    for run_id in run_ids:
        FlowRun.objects.filter(id=run_id).update(uuid=uuid4())
        num_updated += 1

        if num_updated % 1000 == 0:
            print(" > Updated %d of %d flow runs" % (num_updated, len(run_ids)))


def apply_manual():
    from temba.flows.models import FlowRun
    populate_flowrun_uuid(FlowRun)


def apply_as_migration(apps, schema_editor):
    FlowRun = apps.get_model('flows', 'FlowRun')
    populate_flowrun_uuid(FlowRun)


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0107_flowrun_uuid'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration)
    ]
