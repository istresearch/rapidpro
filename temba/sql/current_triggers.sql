-- Generated by collect_sql on 2017-02-03 08:33 UTC

CREATE TRIGGER contact_check_update_trg
   BEFORE UPDATE OF is_test, is_blocked, is_stopped ON contacts_contact
   FOR EACH ROW EXECUTE PROCEDURE contact_check_update();

CREATE TRIGGER temba_broadcast_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON msgs_broadcast
  FOR EACH ROW EXECUTE PROCEDURE temba_broadcast_on_change();

CREATE TRIGGER temba_broadcast_on_truncate_trg
  AFTER TRUNCATE ON msgs_broadcast
  EXECUTE PROCEDURE temba_broadcast_on_change();

CREATE TRIGGER temba_channelevent_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON channels_channelevent
  FOR EACH ROW EXECUTE PROCEDURE temba_channelevent_on_change();

CREATE TRIGGER temba_channelevent_on_truncate_trg
  AFTER TRUNCATE ON channels_channelevent
  EXECUTE PROCEDURE temba_channelevent_on_change();

CREATE TRIGGER temba_channellog_truncate_channelcount
  AFTER TRUNCATE
  ON channels_channellog
  EXECUTE PROCEDURE temba_update_channellog_count();

CREATE TRIGGER temba_channellog_update_channelcount
   AFTER INSERT OR UPDATE OF is_error, channel_id
   ON channels_channellog
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channellog_count();

CREATE TRIGGER temba_flowrun_truncate_flowruncount
  AFTER TRUNCATE
  ON flows_flowrun
  EXECUTE PROCEDURE temba_update_flowruncount();

CREATE TRIGGER temba_flowrun_update_flowruncount
   AFTER INSERT OR DELETE OR UPDATE OF exit_type
   ON flows_flowrun
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowruncount();

CREATE TRIGGER temba_flowstep_truncate_flowpathcount
  AFTER TRUNCATE
  ON flows_flowstep
  EXECUTE PROCEDURE temba_update_flowpathcount();

CREATE TRIGGER temba_flowstep_update_flowpathcount
   AFTER INSERT OR DELETE OR UPDATE OF left_on
   ON flows_flowstep
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowpathcount();

CREATE TRIGGER temba_msg_clear_channelcount
  AFTER TRUNCATE
  ON msgs_msg
  EXECUTE PROCEDURE temba_update_channelcount();

CREATE TRIGGER temba_msg_labels_on_change_trg
   AFTER INSERT OR DELETE ON msgs_msg_labels
   FOR EACH ROW EXECUTE PROCEDURE temba_msg_labels_on_change();

CREATE TRIGGER temba_msg_labels_on_truncate_trg
  AFTER TRUNCATE ON msgs_msg_labels
  EXECUTE PROCEDURE temba_msg_labels_on_change();

CREATE TRIGGER temba_msg_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON msgs_msg
  FOR EACH ROW EXECUTE PROCEDURE temba_msg_on_change();

CREATE TRIGGER temba_msg_on_truncate_trg
  AFTER TRUNCATE ON msgs_msg
  EXECUTE PROCEDURE temba_msg_on_change();

CREATE TRIGGER temba_msg_update_channelcount
   AFTER INSERT OR UPDATE OF direction, msg_type, created_on
   ON msgs_msg
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channelcount();

CREATE TRIGGER temba_when_debit_update_then_update_topupcredits_for_debit
   AFTER INSERT OR DELETE OR UPDATE OF topup_id
   ON orgs_debit
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_topupcredits_for_debit();

CREATE TRIGGER temba_when_msgs_update_then_update_topupcredits
   AFTER INSERT OR DELETE OR UPDATE OF topup_id
   ON msgs_msg
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_topupcredits();

CREATE TRIGGER when_contact_groups_changed_then_update_count_trg
   AFTER INSERT OR DELETE ON contacts_contactgroup_contacts
   FOR EACH ROW EXECUTE PROCEDURE update_group_count();

CREATE TRIGGER when_contact_groups_truncate_then_update_count_trg
  AFTER TRUNCATE ON contacts_contactgroup_contacts
  EXECUTE PROCEDURE update_group_count();

CREATE TRIGGER when_contacts_changed_then_update_groups_trg
   AFTER INSERT OR UPDATE ON contacts_contact
   FOR EACH ROW EXECUTE PROCEDURE update_contact_system_groups();

