# Generated by Django 2.2.10 on 2020-08-10 16:56

import gzip
import json
from urllib.parse import urlparse

import boto3

from django.conf import settings
from django.db import migrations, transaction
from django.utils import timezone

WRITE_BATCH_SIZE = 5000


def s3_client():  # pragma: no cover
    return boto3.Session(
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID, aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    ).client("s3")


def iter_records(archive):  # pragma: no cover
    s3 = s3_client()
    url_parts = urlparse(archive.url)
    try:
        s3_obj = s3.get_object(Bucket=url_parts.netloc.split(".")[0], Key=url_parts.path[1:])
        stream = gzip.GzipFile(fileobj=s3_obj["Body"])

        while True:
            line = stream.readline()
            if not line:
                break

            yield json.loads(line.decode("utf-8"))
    except Exception:
        pass




def calculate_last_seen_from(org):  # pragma: no cover
    # map of contact uuid -> last seen date
    last_seen_by_uuid = {}

    def seen_on(contact_id, date):
        current_last_seen = last_seen_by_uuid.get(contact_id)
        if not current_last_seen or date > current_last_seen:
            last_seen_by_uuid[contact_id] = date

    archives = org.archives.filter(archive_type="message", record_count__gt=0, rollup=None).order_by("start_date")

    num_records = 0
    for archive in archives:
        for record in iter_records(archive):
            if record["direction"] == "in":
                seen_on(record["contact"]["uuid"], record["created_on"])

                num_records += 1
                if num_records % 10000 == 0:  # pragma: no cover
                    print(f"   - Processed {num_records} archived incoming messages")

    print(f"   - Calculated {len(last_seen_by_uuid)} last seen values")

    return last_seen_by_uuid


def populate_last_seen_on_for_org(apps, org):  # pragma: no cover
    Contact = apps.get_model("contacts", "Contact")

    last_seen_by_uuid = calculate_last_seen_from(org)

    while last_seen_by_uuid:
        batch = pop_dict_items(last_seen_by_uuid, WRITE_BATCH_SIZE)

        # get contact UUIDs we actually need to update
        contact_uuids = list(
            Contact.objects.filter(uuid__in=batch.keys(), last_seen_on=None).values_list("uuid", flat=True)
        )

        with transaction.atomic():
            for contact_uuid in contact_uuids:
                Contact.objects.filter(uuid=contact_uuid).update(
                    last_seen_on=batch[contact_uuid], modified_on=timezone.now()
                )

        print(f"   - Updated {len(contact_uuids)} contacts with new last seen values")


def populate_last_seen_on(apps, schema_editor):  # pragma: no cover
    Org = apps.get_model("orgs", "Org")
    num_orgs = Org.objects.filter(is_active=True).count()

    for o, org in enumerate(Org.objects.filter(is_active=True).order_by("id")):
        print(f" > Updating last_seen_on for org '{org.name}' ({o + 1} / {num_orgs})...")

        populate_last_seen_on_for_org(apps, org)


def pop_dict_items(d, count):  # pragma: no cover
    """
    Pop up to count items from the dict d
    """
    items = []
    while len(items) < count:
        try:
            items.append(d.popitem())
        except KeyError:
            break
    return dict(items)


def reverse(apps, schema_editor):  # pragma: no cover
    pass


def apply_manual():  # pragma: no cover
    from django.apps import apps

    populate_last_seen_on(apps, None)


class Migration(migrations.Migration):

    dependencies = [
        ("contacts", "0110_populate_last_seen_on"),
    ]

    operations = [migrations.RunPython(populate_last_seen_on, reverse)]
