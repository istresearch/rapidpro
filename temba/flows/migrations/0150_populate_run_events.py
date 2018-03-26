# -*- coding: utf-8 -*-
# Generated by Django 1.11.6 on 2018-03-23 16:11
from __future__ import absolute_import, division, print_function, unicode_literals

import time
import os

from datetime import timedelta
from django.db import migrations, transaction
from django.db.models import Prefetch
from django.utils import timezone
from django_redis import get_redis_connection
from temba.utils import chunk_list
from uuid import uuid4

CACHE_KEY_HIGHPOINT = 'events_mig_highpoint'
CACHE_KEY_MAX_RUN_ID = 'events_mig_max_run_id'

PATH_STEP_UUID = 'uuid'
PATH_NODE_UUID = 'node_uuid'
PATH_ARRIVED_ON = 'arrived_on'
PATH_EXIT_UUID = 'exit_uuid'
PATH_MAX_STEPS = 100


def serialize_message(msg):
    serialized = {'text': msg.text}

    if msg.uuid:
        serialized['uuid'] = str(msg.uuid)
    if msg.contact_urn_id:
        serialized['urn'] = msg.contact_urn.identity
    if msg.channel_id:
        serialized['channel'] = {'uuid': str(msg.channel.uuid), 'name': msg.channel.name}
    if msg.attachments:
        serialized['attachments'] = msg.attachments

    return serialized


def fill_path_and_events(run):
    # we can re-use exit_uuids calculated in previous migration for actionsets which always have the same exit_uuid
    exit_uuids = {s[PATH_NODE_UUID]: s.get(PATH_EXIT_UUID) for s in run.path}

    run.path = []
    run.events = []
    seen_msgs = set()

    for step in run.steps.all():
        path_step = {
            PATH_STEP_UUID: str(uuid4()),
            PATH_NODE_UUID: step.step_uuid,
            PATH_ARRIVED_ON: step.arrived_on.isoformat(),
        }
        if step.step_type == 'R':
            exit_uuid = step.rule_uuid
        else:
            exit_uuid = exit_uuids.get(step.step_uuid)

        if exit_uuid:
            path_step[PATH_EXIT_UUID] = exit_uuid

        run.path.append(path_step)

        # generate message events for this step
        for msg in sorted(list(step.messages.all()), key=lambda m: m.created_on):
            if msg not in seen_msgs:
                seen_msgs.add(msg)
                run.events.append({
                    'type': 'msg_received' if msg.direction == 'I' else 'msg_created',
                    'created_on': msg.created_on.isoformat(),
                    'step_uuid': path_step[PATH_STEP_UUID],
                    'msg': serialize_message(msg)
                })

        # trim path if necessary
        if len(run.path) > PATH_MAX_STEPS:
            run.path = run.path[len(run.path) - PATH_MAX_STEPS:]

    run.save(update_fields=('events', 'path'))


def backfill_flowrun_events(FlowRun, FlowStep, Msg, Channel, ContactURN):
    cache = get_redis_connection()

    # are we running on just a partition of the runs?
    partition = os.environ.get('PARTITION')
    if partition is not None:
        partition = int(partition)
        if partition < 0 or partition > 3:
            raise ValueError("Partition must be 0-3")

        print("Migrating runs in partition %d" % partition)

    # has this migration been run before but didn't complete?
    highpoint = None
    if partition is not None:
        highpoint = cache.get(CACHE_KEY_HIGHPOINT + (':%d' % partition))
    if highpoint is None:
        highpoint = cache.get(CACHE_KEY_HIGHPOINT)

    highpoint = 0 if highpoint is None else int(highpoint)

    max_run_id = cache.get(CACHE_KEY_MAX_RUN_ID)
    if max_run_id is None:
        max_run = FlowRun.objects.filter(flow__is_active=True).order_by('-id').first()
        if max_run:
            max_run_id = max_run.id
            cache.set(CACHE_KEY_MAX_RUN_ID, max_run_id, 60 * 60 * 24 * 7)
        else:
            return  # no work to do here
    else:
        max_run_id = int(max_run_id)

    if highpoint:
        print("Resuming from previous highpoint at run #%d" % highpoint)

    if max_run_id:
        print("Migrating runs up to run #%d" % max_run_id)

    remaining_estimate = max_run_id - highpoint
    print("Estimated %d runs need to be migrated" % remaining_estimate)

    num_updated = 0
    start = time.time()

    # we want to prefetch step messages with each flow run
    steps_prefetch = Prefetch('steps', queryset=FlowStep.objects.order_by('id'))
    steps_messages_prefetch = Prefetch('steps__messages', queryset=Msg.objects.defer('metadata'))
    steps_messages_channel_prefetch = Prefetch('steps__messages__channel', queryset=Channel.objects.only('id', 'name', 'uuid'))
    steps_messages_urn_prefetch = Prefetch('steps__messages__contact_urn', queryset=ContactURN.objects.only('id', 'identity'))

    for run_id_batch in chunk_list(range(highpoint, max_run_id + 1), 4000):
        with transaction.atomic():
            if partition is not None:
                run_id_batch = [r_id for r_id in run_id_batch if ((r_id + partition) % 4 == 0)]

            batch = (
                FlowRun.objects
                .filter(id__in=run_id_batch).order_by('id')
                .defer('results', 'fields')
                .prefetch_related(
                    steps_prefetch,
                    steps_messages_prefetch,
                    steps_messages_channel_prefetch,
                    steps_messages_urn_prefetch,
                )
            )

            for run in batch:
                fill_path_and_events(run)

                highpoint = run.id
                if partition is not None:
                    cache.set(CACHE_KEY_HIGHPOINT + (":%d" % partition), str(run.id), 60 * 60 * 24 * 7)
                else:
                    cache.set(CACHE_KEY_HIGHPOINT, str(run.id), 60 * 60 * 24 * 7)

        num_updated += len(run_id_batch)
        updated_per_sec = num_updated / (time.time() - start)

        # figure out estimated time remaining
        num_remaining = ((max_run_id - highpoint) // 4) if partition is not None else (max_run_id - highpoint)
        time_remaining = (num_remaining / updated_per_sec) if updated_per_sec > 0 else 0
        finishes = timezone.now() + timedelta(seconds=time_remaining)
        status = " > Updated %d runs of ~%d (%2.2f per sec) Est finish: %s" % (num_updated, remaining_estimate, updated_per_sec, finishes)

        if partition is not None:
            status += ' [PARTITION %d]' % partition

        print(status)

    print("Run events migration completed in %d mins" % (int(time.time() - start) // 60))


def apply_manual():
    from temba.channels.models import Channel
    from temba.contacts.models import ContactURN
    from temba.flows.models import FlowRun, FlowStep
    from temba.msgs.models import Msg
    backfill_flowrun_events(FlowRun, FlowStep, Msg, Channel, ContactURN)


def apply_as_migration(apps, schema_editor):
    FlowRun = apps.get_model('flows', 'FlowRun')
    FlowStep = apps.get_model('flows', 'FlowStep')
    Msg = apps.get_model('msgs', 'Msg')
    Channel = apps.get_model('channels', 'Channel')
    ContactURN = apps.get_model('contacts', 'ContactURN')
    backfill_flowrun_events(FlowRun, FlowStep, Msg, Channel, ContactURN)


def clear_migration(apps, schema_editor):
    r = get_redis_connection()
    r.delete('events_mig_max_run_id')
    r.delete('events_mig_highpoint')
    r.delete('events_mig_highpoint:0')
    r.delete('events_mig_highpoint:1')
    r.delete('events_mig_highpoint:2')
    r.delete('events_mig_highpoint:3')


class Migration(migrations.Migration):

    dependencies = [
        ('flows', '0149_update_path_trigger'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration, clear_migration)
    ]
