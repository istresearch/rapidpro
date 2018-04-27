# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-10-20 17:54
from __future__ import absolute_import, division, print_function, unicode_literals

from django.db import migrations
from temba.utils import chunk_list


def migrate_flows_forward():
    from temba.flows.models import Flow

    flow_ids = list(Flow.objects.filter(is_active=True).values_list('id', flat=True))
    total = len(flow_ids)
    updated = 0
    for id_batch in chunk_list(flow_ids, 1000):
        for flow in Flow.objects.filter(id__in=id_batch):

            # bug out if we have any dependencies already
            if flow.group_dependencies.all().exists():
                continue
            if flow.flow_dependencies.all().exists():
                continue
            if flow.field_dependencies.all().exists():
                continue

            flow.update_dependencies()

        updated += len(id_batch)
        print("Updated flows: %d of %d" % (updated, total))


def apply_manual():
    migrate_flows_forward()


def apply_as_migration(apps, schema_editor):
    migrate_flows_forward()


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0115_auto_20171023_1951'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration)
    ]
