CREATE OR REPLACE TRIGGER temba_broadcast_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON msgs_broadcast
  FOR EACH ROW EXECUTE PROCEDURE temba_broadcast_on_change();

CREATE OR REPLACE TRIGGER temba_channelevent_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON channels_channelevent
  FOR EACH ROW EXECUTE PROCEDURE temba_channelevent_on_change();

CREATE OR REPLACE TRIGGER temba_channellog_update_channelcount
   AFTER INSERT OR DELETE OR UPDATE OF is_error, channel_id
   ON channels_channellog
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channellog_count();

CREATE OR REPLACE TRIGGER temba_flowrun_delete
    AFTER DELETE ON flows_flowrun
    FOR EACH ROW EXECUTE PROCEDURE temba_flowrun_delete();

CREATE OR REPLACE TRIGGER temba_flowrun_insert
    AFTER INSERT ON flows_flowrun
    FOR EACH ROW EXECUTE PROCEDURE temba_flowrun_insert();

/*EDIT: do not create; replaced in flows, 0274_replace_exit_type.py
CREATE OR REPLACE TRIGGER temba_flowrun_path_change
    AFTER UPDATE OF path, is_active ON flows_flowrun
    FOR EACH ROW EXECUTE PROCEDURE temba_flowrun_path_change();
*/
/*EDIT: do not create; replaced in flows, 0273_delete_from_results.py
CREATE OR REPLACE TRIGGER temba_flowrun_update_flowcategorycount
   AFTER INSERT OR DELETE OR UPDATE OF results
   ON flows_flowrun
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowcategorycount();
*/
/*EDIT: do not create; dropped in flows, 0274_replace_exit_type.py
CREATE OR REPLACE TRIGGER temba_flowrun_update_flowruncount
   AFTER INSERT OR DELETE OR UPDATE OF exit_type
   ON flows_flowrun
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowruncount();
*/
/*EDIT: do not create; dropped in flows, 0273_delete_from_results.py
CREATE OR REPLACE TRIGGER temba_flowrun_update_flowstartcount
   AFTER INSERT OR DELETE OR UPDATE OF start_id
   ON flows_flowrun
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_flowstartcount();
*/
CREATE OR REPLACE TRIGGER temba_msg_labels_on_change_trg
   AFTER INSERT OR DELETE ON msgs_msg_labels
   FOR EACH ROW EXECUTE PROCEDURE temba_msg_labels_on_change();

CREATE OR REPLACE TRIGGER temba_msg_on_change_trg
  AFTER INSERT OR UPDATE OR DELETE ON msgs_msg
  FOR EACH ROW EXECUTE PROCEDURE temba_msg_on_change();

CREATE OR REPLACE TRIGGER temba_msg_update_channelcount
   AFTER INSERT OR DELETE OR UPDATE OF direction, msg_type, created_on
   ON msgs_msg
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channelcount();

CREATE OR REPLACE TRIGGER temba_when_debit_update_then_update_topupcredits_for_debit
   AFTER INSERT OR DELETE OR UPDATE OF topup_id
   ON orgs_debit
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_topupcredits_for_debit();

CREATE OR REPLACE TRIGGER temba_when_msgs_update_then_update_topupcredits
   AFTER INSERT OR DELETE OR UPDATE OF topup_id
   ON msgs_msg
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_topupcredits();

CREATE OR REPLACE TRIGGER when_contact_groups_changed_then_update_count_trg
   AFTER INSERT OR DELETE ON contacts_contactgroup_contacts
   FOR EACH ROW EXECUTE PROCEDURE update_group_count();

CREATE OR REPLACE TRIGGER when_contacts_changed_then_update_groups_trg
   AFTER INSERT OR UPDATE ON contacts_contact
   FOR EACH ROW EXECUTE PROCEDURE update_contact_system_groups();
