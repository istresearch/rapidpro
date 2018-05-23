# Generated by Django 1.11.6 on 2017-12-07 15:26

from django.db import migrations


class Migration(migrations.Migration):
    atomic = False

    INDEX_SQL = """
    CREATE INDEX CONCURRENTLY flows_flowrun_contact_flow_created_on_id_idx ON flows_flowrun(contact_id, flow_id, created_on desc, id desc) WHERE is_active = TRUE;
    """

    dependencies = [
        ('flows', '0130_auto_20171128_1618'),
    ]

    operations = [
        migrations.RunSQL(INDEX_SQL)
    ]
