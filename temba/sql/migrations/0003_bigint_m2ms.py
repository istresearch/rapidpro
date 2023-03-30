# Generated by Django 2.2.10 on 2021-01-05 19:36

from django.db import migrations

SQL = """
ALTER TABLE "contacts_contactgroup_contacts" ALTER COLUMN "id" TYPE bigint USING "id"::bigint;
ALTER TABLE "msgs_broadcast_contacts" ALTER COLUMN "id" TYPE bigint USING "id"::bigint;
ALTER TABLE "msgs_msg_labels" ALTER COLUMN "msg_id" TYPE bigint USING "msg_id"::bigint;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("sql", "0002_updates"),
    ]

    operations = [migrations.RunSQL(SQL)]
