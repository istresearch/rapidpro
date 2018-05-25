# Generated by Django 1.11.6 on 2017-12-14 19:09

from django.db import migrations


SQL = """
CREATE INDEX CONCURRENTLY flows_flowrun_org_current_node_uuid_active_only
ON flows_flowrun(org_id, current_node_uuid)
WHERE is_active = TRUE;"""


class Migration(migrations.Migration):

    atomic = False

    dependencies = [("flows", "0139_fix_results")]

    operations = [migrations.RunSQL(SQL)]
