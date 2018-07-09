# Generated by Django 1.11.6 on 2018-05-04 19:12

import django.db.models.deletion
from django.db import migrations, models

SQL = """
-- index for fast fetching of unsquashed rows
CREATE INDEX flows_flowstartcount_unsquashed
ON flows_flowstartcount(start_id) WHERE NOT is_squashed;

----------------------------------------------------------------------
-- Inserts a new flowstart_count
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION
  temba_insert_flowstartcount(_start_id INT, _count INT)
RETURNS VOID AS $$
BEGIN
  IF _start_id IS NOT NULL THEN
    INSERT INTO flows_flowstartcount("start_id", "count", "is_squashed")
    VALUES(_start_id, _count, FALSE);
  END IF;
END;
$$ LANGUAGE plpgsql;

----------------------------------------------------------------------
-- Increments or decrements our counts for each exit type
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_update_flowruncount() RETURNS TRIGGER AS $$
BEGIN
  -- FlowRun being added
  IF TG_OP = 'INSERT' THEN
     -- Is this a test contact, ignore
     IF temba_contact_is_test(NEW.contact_id) THEN
       RETURN NULL;
     END IF;

    -- Increment appropriate type
    PERFORM temba_insert_flowruncount(NEW.flow_id, NEW.exit_type, 1);

  -- FlowRun being removed
  ELSIF TG_OP = 'DELETE' THEN
     -- Is this a test contact, ignore
     IF temba_contact_is_test(OLD.contact_id) THEN
       RETURN NULL;
     END IF;

    PERFORM temba_insert_flowruncount(OLD.flow_id, OLD.exit_type, -1);

  -- Updating exit type
  ELSIF TG_OP = 'UPDATE' THEN
     -- Is this a test contact, ignore
     IF temba_contact_is_test(NEW.contact_id) THEN
       RETURN NULL;
     END IF;

    PERFORM temba_insert_flowruncount(OLD.flow_id, OLD.exit_type, -1);
    PERFORM temba_insert_flowruncount(NEW.flow_id, NEW.exit_type, 1);
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

----------------------------------------------------------------------
-- Increments or decrements our start counts for each exit type
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_update_flowstartcount() RETURNS TRIGGER AS $$
BEGIN
  -- FlowRun being added
  IF TG_OP = 'INSERT' THEN
    PERFORM temba_insert_flowstartcount(NEW.start_id, 1);

  -- FlowRun being removed
  ELSIF TG_OP = 'DELETE' THEN
    PERFORM temba_insert_flowstartcount(OLD.start_id, -1);

  -- Updating exit type
  ELSIF TG_OP = 'UPDATE' THEN
    PERFORM temba_insert_flowstartcount(OLD.start_id, -1);
    PERFORM temba_insert_flowstartcount(NEW.start_id, 1);
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER temba_flowrun_update_flowstartcount
   AFTER INSERT OR DELETE OR UPDATE OF start_id
   ON flows_flowrun
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowstartcount();
"""


class Migration(migrations.Migration):

    dependencies = [("flows", "0152_auto_20180502_1603")]

    operations = [
        migrations.CreateModel(
            name="FlowStartCount",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "is_squashed",
                    models.BooleanField(default=False, help_text="Whether this row was created by squashing"),
                ),
                ("count", models.IntegerField(default=0)),
                (
                    "start",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, related_name="counts", to="flows.FlowStart"
                    ),
                ),
            ],
            options={"abstract": False},
        ),
        migrations.RunSQL(SQL),
    ]
