# Generated by Django 2.1.8 on 2019-05-29 15:57

from django.db import migrations

from temba import mailroom


def populate_flow_metadata(apps, schema_editor):
    Flow = apps.get_model("flows", "Flow")
    FlowRevision = apps.get_model("flows", "FlowRevision")

    client = mailroom.get_client()

    num_updated = 0
    for flow in Flow.objects.filter(is_active=True):
        # get our last revision
        revision = FlowRevision.objects.filter(flow=flow).order_by("-revision").first()

        # validate it
        try:
            validated_definition = client.flow_validate(None, revision.definition)

            flow.metadata = {
                "results": validated_definition["_results"],
                "dependencies": validated_definition["_dependencies"],
                "waiting_exit_uuids": validated_definition["_waiting_exits"],
            }
            flow.save(update_fields=["metadata"])

        except mailroom.FlowValidationException as e:
            print(f"Error validating flow: {flow.id} - {e}")

        num_updated += 1
        if num_updated % 1000 == 0:
            print(f"Updated {num_updated} flow metadata")


def apply_manual():
    from django.apps import apps

    populate_flow_metadata(apps, None)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [("flows", "0197_update_categorycount_trigger")]

    operations = [migrations.RunPython(populate_flow_metadata, reverse)]
