# Generated by Django 2.2.4 on 2019-11-20 19:43

from django.db import migrations


def trim_flow_revisions(apps, schema_editor):  # pragma: no cover
    from temba.flows.models import FlowRevision

    Flow = apps.get_model("flows", "Flow")

    for flow in Flow.objects.all().only("id", "name"):
        trimmed = FlowRevision.trim_for_flow(flow.id)
        print(trimmed, flow.name, flow.id)


def reverse(apps, schema_editor):  # pragma: no cover
    pass


def apply_manual():  # pragma: no cover
    from django.apps import apps

    trim_flow_revisions(apps, None)


class Migration(migrations.Migration):

    dependencies = [("flows", "0220_auto_20191112_2255")]

    operations = [migrations.RunPython(trim_flow_revisions, reverse)]
