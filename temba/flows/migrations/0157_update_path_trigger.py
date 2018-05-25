# Generated by Django 1.11.6 on 2018-05-21 22:12

from django.db import migrations


SQL = """
----------------------------------------------------------------------
-- Inserts a new flowpathrecentrun
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_insert_flowpathrecentrun(_from_uuid UUID, _from_step_uuid UUID, _to_uuid UUID, _to_step_uuid UUID, _run_id INTEGER, _visited_on TIMESTAMPTZ) RETURNS VOID AS $$
  BEGIN
    INSERT INTO flows_flowpathrecentrun("from_uuid", "from_step_uuid", "to_uuid", "to_step_uuid", "run_id", "visited_on")
      VALUES(_from_uuid, _from_step_uuid, _to_uuid, _to_step_uuid, _run_id, _visited_on);
  END;
$$ LANGUAGE plpgsql;


----------------------------------------------------------------------
-- Handles changes relating to a flow run's path
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_flowrun_path_change() RETURNS TRIGGER AS $$
DECLARE
  p INT;
  _old_is_active BOOL;
  _old_path TEXT;
  _new_path TEXT;
  _old_path_json JSONB;
  _new_path_json JSONB;
  _old_path_len INT;
  _new_path_len INT;
BEGIN
  -- Handles one of the following changes to a flow run:
  --  1. flow path unchanged and is_active becomes false (run interrupted or expired)
  --  2. flow path added to and is_active becomes false (run completed)
  --  3. flow path added to and is_active remains true (run continues)
  --  4. deletion
  --

  -- restrict changes to runs
  IF TG_OP = 'UPDATE' THEN
    IF NEW.is_active AND NOT OLD.is_active THEN RAISE EXCEPTION 'Cannot re-activate an inactive flow run'; END IF;

    -- TODO re-enable after migration to populate run events
    -- IF NOT OLD.is_active AND NEW.path != OLD.path THEN RAISE EXCEPTION 'Cannot modify path on an inactive flow run'; END IF;
  END IF;

  IF TG_OP = 'UPDATE' OR TG_OP = 'DELETE' THEN
    _old_is_active := OLD.is_active;
    _old_path := OLD.path;
  END IF;

  IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
    -- ignore test contacts
    IF temba_contact_is_test(NEW.contact_id) THEN RETURN NULL; END IF;

    _new_path := NEW.path;

    -- don't differentiate between empty array and NULL
    IF _old_path IS NULL THEN _old_path := '[]'; END IF;
    IF _new_path IS NULL THEN _new_path := '[]'; END IF;

    _old_path_json := _old_path::jsonb;
    _new_path_json := _new_path::jsonb;
    _old_path_len := jsonb_array_length(_old_path_json);
    _new_path_len := jsonb_array_length(_new_path_json);

    -- if there are no changes that effect path/node counts, bail
    IF TG_OP = 'UPDATE'
        AND _old_path_len = _new_path_len
        AND COALESCE(_old_path_json->(_old_path_len-1)->>'exit_uuid', '') = COALESCE(_new_path_json->(_new_path_len-1)->>'exit_uuid', '')
        AND NEW.is_active = OLD.is_active
    THEN
      RETURN NULL;
    END IF;

    -- we don't support rewinding run paths, so the new path must be longer than the old
    IF _new_path_len < _old_path_len THEN RAISE EXCEPTION 'Cannot rewind a flow run path'; END IF;

    -- update the node counts
    IF _old_path_len > 0 AND _old_is_active THEN
      PERFORM temba_insert_flownodecount(NEW.flow_id, UUID(_old_path_json->(_old_path_len-1)->>'node_uuid'), -1);
    END IF;

    IF _new_path_len > 0 AND NEW.is_active THEN
      PERFORM temba_insert_flownodecount(NEW.flow_id, UUID(_new_path_json->(_new_path_len-1)->>'node_uuid'), 1);
    END IF;

    -- if we have old steps, we start at the end of the old path
    IF _old_path_len > 0 THEN p := _old_path_len; ELSE p := 1; END IF;

    LOOP
      EXIT WHEN p >= _new_path_len;
      PERFORM temba_insert_flowpathcount(
          NEW.flow_id,
          UUID(_new_path_json->(p-1)->>'exit_uuid'),
          UUID(_new_path_json->p->>'node_uuid'),
          timestamptz(_new_path_json->p->>'arrived_on'),
          1
      );
      PERFORM temba_insert_flowpathrecentrun(
        UUID(_new_path_json->(p-1)->>'exit_uuid'),
        UUID(_new_path_json->(p-1)->>'uuid'),
        UUID(_new_path_json->p->>'node_uuid'),
        UUID(_new_path_json->p->>'uuid'),
        NEW.id,
        timestamptz(_new_path_json->p->>'arrived_on')
      );
      p := p + 1;
    END LOOP;

  ELSIF TG_OP = 'DELETE' THEN
    -- ignore test contacts
    IF temba_contact_is_test(OLD.contact_id) THEN RETURN NULL; END IF;

    -- do nothing if path was empty
    IF _old_path IS NULL OR _old_path = '[]' THEN RETURN NULL; END IF;

    -- parse path as JSON
    _old_path_json := _old_path::json;
    _old_path_len := jsonb_array_length(_old_path_json);

    -- decrement node count at last node in this path if this was an active run
    IF _old_is_active THEN
      PERFORM temba_insert_flownodecount(OLD.flow_id, UUID(_old_path_json->(_old_path_len-1)->>'node_uuid'), -1);
    END IF;

    -- decrement all path counts
    p := 1;
    LOOP
      EXIT WHEN p >= _old_path_len;

      -- it's possible that steps from old flows don't have exit_uuid
      IF (_old_path_json->(p-1)->'exit_uuid') IS NOT NULL THEN
        PERFORM temba_insert_flowpathcount(
          OLD.flow_id,
          UUID(_old_path_json->(p-1)->>'exit_uuid'),
          UUID(_old_path_json->p->>'node_uuid'),
          timestamptz(_old_path_json->p->>'arrived_on'),
          -1
        );
      END IF;

      p := p + 1;
    END LOOP;
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [("flows", "0156_auto_20180521_2211")]

    operations = [migrations.RunSQL(SQL)]
