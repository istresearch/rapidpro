# Generated by Django 2.2.4 on 2020-04-09 21:41

from django.db import migrations, transaction
from django.db.models import Prefetch, Q

BATCH_SIZE = 5000


def populate_flowstart_org(apps, schema_editor):  # pragma: no cover
    Flow = apps.get_model("flows", "Flow")
    FlowStart = apps.get_model("flows", "FlowStart")

    flow_prefetch = Prefetch("flow", Flow.objects.only("id", "org_id"))
    starts = (
        FlowStart.objects.filter(Q(org=None) | Q(modified_on=None))
        .only("id", "flow", "org_id", "created_on", "modified_on")
        .prefetch_related(flow_prefetch)
    )

    num_updated = 0
    max_id = -1
    while True:
        batch = list(starts.filter(id__gt=max_id).order_by("id")[:BATCH_SIZE])
        if not batch:
            break

        with transaction.atomic():
            for start in batch:
                start.org_id = start.flow.org_id
                start.modified_on = start.modified_on or start.created_on
                start.save(update_fields=("org_id", "modified_on"))

        num_updated += len(batch)
        print(f" > Updated {num_updated} flow starts with NULL org or modified_on")

        max_id = batch[-1].id


def reverse(apps, schema_editor):  # pragma: no cover
    pass


def apply_manual():  # pragma: no cover
    from django.apps import apps

    populate_flowstart_org(apps, None)


class Migration(migrations.Migration):

    dependencies = [("flows", "0226_add_flowstart_org")]

    operations = [migrations.RunPython(populate_flowstart_org, reverse)]