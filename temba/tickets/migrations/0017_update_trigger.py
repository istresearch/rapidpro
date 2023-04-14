# Generated by Django 2.2.20 on 2021-07-28 21:24

from django.db import migrations

SQL = """
----------------------------------------------------------------------
-- Trigger procedure to update user and system labels on column changes
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_ticket_on_change() RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN -- new ticket inserted
    PERFORM temba_insert_ticketcount(NEW.org_id, NEW.assignee_id, NEW.status, 1);
    IF NEW.status = 'O' THEN
      UPDATE contacts_contact SET ticket_count = ticket_count + 1, modified_on = NOW() WHERE id = NEW.contact_id;
    END IF;
  ELSIF TG_OP = 'UPDATE' THEN -- existing ticket updated
    IF OLD.assignee_id IS DISTINCT FROM NEW.assignee_id OR OLD.status != NEW.status THEN
      PERFORM temba_insert_ticketcount(OLD.org_id, OLD.assignee_id, OLD.status, -1);
      PERFORM temba_insert_ticketcount(NEW.org_id, NEW.assignee_id, NEW.status, 1);
    END IF;
    IF OLD.status = 'O' AND NEW.status = 'C' THEN -- ticket closed
      UPDATE contacts_contact SET ticket_count = ticket_count - 1, modified_on = NOW() WHERE id = OLD.contact_id;
    ELSIF OLD.status = 'C' AND NEW.status = 'O' THEN -- ticket reopened
      UPDATE contacts_contact SET ticket_count = ticket_count + 1, modified_on = NOW() WHERE id = OLD.contact_id;
    END IF;
  ELSIF TG_OP = 'DELETE' THEN -- existing ticket deleted
    PERFORM temba_insert_ticketcount(OLD.org_id, OLD.assignee_id, OLD.status, -1);
    IF OLD.status = 'O' THEN -- open ticket deleted
      UPDATE contacts_contact SET ticket_count = ticket_count - 1, modified_on = NOW() WHERE id = OLD.contact_id;
    END IF;
  END IF;
  RETURN NULL;
END;
$$ LANGUAGE plpgsql;
"""


class Migration(migrations.Migration):

    dependencies = [
        ("tickets", "0016_auto_20210727_1716"),
        ("contacts", "0140_zeroize_ticket_count"),
    ]

    operations = [migrations.RunSQL(SQL)]