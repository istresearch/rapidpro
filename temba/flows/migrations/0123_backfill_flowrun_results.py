# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-11-02 15:39
from __future__ import unicode_literals

from django.db import migrations
from temba.utils import chunk_list
import json
import regex
from datetime import datetime
import six
import time
from django_redis import get_redis_connection
from django.utils import timezone
from datetime import timedelta

# these are called out here because we can't reference the real FlowRun in this migration
RESULT_NAME = 'name'
RESULT_NODE_UUID = 'node_uuid'
RESULT_CATEGORY = 'category'
RESULT_CATEGORY_LOCALIZED = 'category_localized'
RESULT_VALUE = 'value'
RESULT_INPUT = 'input'
RESULT_CREATED_ON = 'created_on'


# same reason, we need this but can't use the real FlowRun object
def serialize_value(value):
    """
    Utility method to give the serialized value for the passed in value
    """
    from temba.locations.models import AdminBoundary

    if value is None:
        return None

    if isinstance(value, datetime):
        return value.isoformat()
    elif isinstance(value, AdminBoundary):
        return value.as_path()
    else:
        return six.text_type(value)


def backfill_flowrun_results(Flow, FlowRun, FlowStep, RuleSet, Value):
    # For each flow we need to:
    # 1) get all our rulesets so we can map labels and uuids correctly
    # 2) get all runs in batches of 1000
    # 3) get all steps and values in that batch
    # 4) write results for each

    cache = get_redis_connection()

    # get all active flow ids
    flow_ids = Flow.objects.filter(is_active=True).values_list('id', flat=True)
    if flow_ids:
        print("Found %d flows to migrate results for" % len(flow_ids))

        # flow runs past this point are being written with results, don't migrate them again
        highwater = cache.get("results_mig_highwater")
        if not highwater:
            last = FlowRun.objects.all().order_by('-id').first()
            if last:
                highwater = last.id
                cache.set("results_mig_highwater", highwater)

        # for estimation, figure out total # of runs
        flowrun_count = FlowRun.objects.filter(flow__is_active=True).count()
        mig_count = cache.get("results_mig_count")
        update_count = int(mig_count) if mig_count else 0
        current_update_count = 0
        start = time.time()

        for flow_chunk in chunk_list(flow_ids, 100):
            for flow in Flow.objects.filter(id__in=flow_chunk):
                # figure out if we already migrated this flow
                migrated = cache.sismember("results_mig", flow.id)
                if migrated:
                    continue

                # build a our mapping of ruleset uuid to category name
                id_to_ruleset = {r.id: r for r in RuleSet.objects.filter(flow=flow).only('id', 'label', 'uuid')}
                ruleset_uuids = [r.uuid for r in id_to_ruleset.values()]

                run_ids = FlowRun.objects.filter(flow=flow, id__lt=highwater).values_list('id', flat=True)
                for run_chunk in chunk_list(run_ids, 1000):
                    runs = FlowRun.objects.filter(id__in=run_chunk).prefetch_related('values')

                    # get all the steps across these runs
                    steps = FlowStep.objects.filter(run_id__in=run_chunk, step_uuid__in=ruleset_uuids).order_by('-id').prefetch_related('messages')
                    step_text = {}
                    for step in steps:
                        key = "%d:%s" % (step.run_id, step.step_uuid)

                        # we only log the most recent
                        if key not in step_text:
                            msg = step.messages.first()
                            if msg:
                                step_text[key] = msg.text
                            else:
                                step_text[key] = ""

                    for run in runs:
                        results = {}
                        for value in run.values.all():
                            if not value.ruleset_id or value.ruleset_id not in id_to_ruleset:
                                continue

                            rs = id_to_ruleset[value.ruleset_id]
                            result = {
                                RESULT_NAME: rs.label,
                                RESULT_CATEGORY: value.category,
                                RESULT_NODE_UUID: rs.uuid,
                                RESULT_CREATED_ON: serialize_value(value.modified_on),
                            }

                            # serialize our value in our new string formats based on what value we have
                            if value.datetime_value:
                                result[RESULT_VALUE] = serialize_value(value.datetime_value)
                            elif value.location_value:
                                result[RESULT_VALUE] = serialize_value(value.location_value)
                            elif value.decimal_value:
                                result[RESULT_VALUE] = serialize_value(value.decimal_value)
                            else:
                                result[RESULT_VALUE] = serialize_value(value.string_value)

                            # finally we need to figure out the input for this value, this is only stored on FlowStep
                            result_input = step_text.get("%d:%s" % (value.run_id, rs.uuid))
                            if result_input:
                                result[RESULT_INPUT] = result_input

                            key = regex.sub(r'[^a-z0-9]+', '_', rs.label.lower(), regex.V0)
                            results[key] = result

                        # if we found results, update this run
                        if results:
                            run.results = json.dumps(results)
                            run.save(update_fields=['results'])

                    update_count += len(runs)
                    current_update_count += len(runs)

                    # figure out our rate
                    rate = (time.time() - start) / current_update_count

                    # figure out per second
                    per_sec = 1 / rate

                    # figure out estimated time remaining
                    mins = ((flowrun_count - update_count) / per_sec) / 60
                    finished = timezone.now() + timedelta(minutes=mins)

                    print("Updated %d runs of %d (%2.2f per sec) Est finish: %s" % (update_count, flowrun_count, per_sec, finished))

                # mark this flow's results as migrated (new runs and values are already good)
                cache.sadd("results_mig", flow.id)
                cache.incrby("results_mig_count", len(run_ids))

                # clear this key after 7 days of inactivity
                cache.expire("results_mig", 3600 * 24 * 30)
                cache.expire("results_mig_count", 3600 * 24 * 30)
                cache.expire("results_mig_highwater", 3600 * 24 * 30)


def apply_manual():
    from temba.flows.models import Flow, FlowRun, FlowStep, RuleSet
    from temba.values.models import Value
    backfill_flowrun_results(Flow, FlowRun, FlowStep, RuleSet, Value)


def apply_as_migration(apps, schema_editor):
    Flow = apps.get_model('flows', 'Flow')
    FlowRun = apps.get_model('flows', 'FlowRun')
    FlowStep = apps.get_model('flows', 'FlowStep')
    RuleSet = apps.get_model('flows', 'RuleSet')
    Value = apps.get_model('values', 'Value')
    backfill_flowrun_results(Flow, FlowRun, FlowStep, RuleSet, Value)


def undo_migration(apps, schema_editor):
    # this just clears out all our redis keys so we recalculate everything
    cache = get_redis_connection()
    cache.delete("results_mig", 3600 * 24 * 30)
    cache.delete("results_mig_count", 3600 * 24 * 30)
    cache.delete("results_mig_highwater", 3600 * 24 * 30)


class Migration(migrations.Migration):

    dependencies = [
        ('values', '0012_auto_20170606_1326'),
        ('flows', '0122_auto_20171101_2041'),
    ]

    operations = [
        migrations.RunPython(apply_as_migration, undo_migration)
    ]
