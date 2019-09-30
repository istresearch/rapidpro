# Generated by Django 2.2.4 on 2019-08-01 21:32

from uuid import uuid4

from django.db import migrations, transaction

BATCH_SIZE = 5000


def populate_session_uuids(apps, schema_editor):  # pragma: no cover
    FlowSession = apps.get_model("flows", "FlowSession")

    num_updated = 0
    max_id = -1
    while True:
        batch = list(
            FlowSession.objects.filter(uuid=None, id__gt=max_id).only("id", "uuid").order_by("id")[:BATCH_SIZE]
        )
        if not batch:
            break

        with transaction.atomic():
            for session in batch:
                session.uuid = str(uuid4())
                session.save(update_fields=("uuid",))

        num_updated += len(batch)
        print(f" > Updated {num_updated} flow sessions with a UUID")

        max_id = batch[-1].id


def reverse(apps, schema_editor):  # pragma: no cover
    pass


def apply_manual():  # pragma: no cover
    from django.apps import apps

    populate_session_uuids(apps, None)


class Migration(migrations.Migration):

    dependencies = [("flows", "0210_drop_action_log")]

    operations = [migrations.RunPython(populate_session_uuids, reverse)]
