# Created by hand

from django.db import migrations


class Migration(migrations.Migration):

    # did not have 0002 at all during last merge, trying to avoid:
    # InconsistentMigrationHistory: Migration flows.0247_auto_20210126_1834 is applied before its dependency sql.0002_updates
    dependencies = [
        ("sql", "0003_bigint_m2ms"),
        ("sql", "0002_updates"),
    ]

    operations = [
        migrations.RunSQL("DROP FUNCTION temba_flow_for_run(_run_id INT);"),
    ]
