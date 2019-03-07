# Generated by Django 2.1.5 on 2019-03-07 16:28

import regex

from django.db import migrations


def label_to_slug(label):
    return regex.sub(r"[^a-z0-9]+", "_", label.lower(), regex.V0)


def extract_results(flow):
    print("extracting results for flow %s" % flow.name)
    results = {}

    for rs in flow.rule_sets.all():
        if rs.label:
            key = label_to_slug(rs.label)

            if key not in results:
                results[key] = {"names": []}

            if rs.label not in results[key]["names"]:
                results[key]["names"].append(rs.label)

    return results


def populate_results(apps, schema_editor):
    Flow = apps.get_model("flows", "Flow")

    num_updated = 0
    for flow in Flow.objects.filter(results__isnull=True).prefetch_related("rule_sets"):
        flow.results = extract_results(flow)
        flow.save(update_fields=("results",))

        if num_updated % 1000 == 0:
            print(f"Updated {num_updated} flows with results")
        num_updated += 1


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("flows", "0195_flow_results")]

    operations = [migrations.RunPython(populate_results, reverse)]
