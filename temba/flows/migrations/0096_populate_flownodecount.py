# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-03-30 12:50
from __future__ import unicode_literals

from django.db import migrations


def do_populate(FlowStep, FlowNodeCount):
    nodes = list(FlowStep.objects.filter(left_on=None, run__is_active=True).distinct('step_uuid').values_list('run__flow_id', 'step_uuid'))

    if nodes:
        print("Fetched %d node UUIDs with active contacts" % len(nodes))

    counts = []
    for flow_id, node_uuid in nodes:
        contact_count = FlowStep.objects.filter(step_uuid=node_uuid, left_on=None,
                                                run__is_active=True, contact__is_test=False).count()

        FlowNodeCount.objects.filter(flow_id=flow_id, node_uuid=node_uuid).delete()
        counts.append(FlowNodeCount(flow_id=flow_id, node_uuid=node_uuid, count=contact_count))

    FlowNodeCount.objects.bulk_create(counts, batch_size=5000)


def populate_flownodecount(apps, schema_editor):
    FlowStep = apps.get_model('flows', 'FlowStep')
    FlowNodeCount = apps.get_model('flows', 'FlowNodeCount')

    do_populate(FlowStep, FlowNodeCount)


def apply_manual():
    from temba.flows.models import FlowStep, FlowNodeCount

    do_populate(FlowStep, FlowNodeCount)


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0095_clear_old_flow_stat_cache'),
    ]

    operations = [
        migrations.RunPython(populate_flownodecount)
    ]
