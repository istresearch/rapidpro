----------------------------------------------------------------------
-- Deprecated functions
----------------------------------------------------------------------
DROP FUNCTION IF EXISTS temba_increment_channelcount();
DROP FUNCTION IF EXISTS temba_decrement_channelcount();
DROP FUNCTION IF EXISTS temba_maybe_squash_channelcount();

----------------------------------------------------------------------
-- Inserts a new channelcount row with the given values
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_insert_channelcount(_channel_id INTEGER, _count_type VARCHAR(2), _count_day DATE, _count INT) RETURNS VOID AS $$
  BEGIN
    INSERT INTO channels_channelcount("channel_id", "count_type", "day", "count", "is_squashed")
      VALUES(_channel_id, _count_type, _count_day, _count, FALSE);
  END;
$$ LANGUAGE plpgsql;

----------------------------------------------------------------------
-- Manages keeping track of the # of messages in our channel log
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_update_channellog_count() RETURNS TRIGGER AS $$
BEGIN
  -- ChannelLog being added
  IF TG_OP = 'INSERT' THEN
    -- Error, increment our error count
    IF NEW.is_error THEN
      PERFORM temba_insert_channelcount(NEW.channel_id, 'LE', NULL::date, 1);
    -- Success, increment that count instead
    ELSE
      PERFORM temba_insert_channelcount(NEW.channel_id, 'LS', NULL::date, 1);
    END IF;

  -- Updating is_error is forbidden
  ELSIF TG_OP = 'UPDATE' THEN
    RAISE EXCEPTION 'Cannot update is_error or channel_id on ChannelLog events';

  -- Table being cleared, reset all counts
  ELSIF TG_OP = 'TRUNCATE' THEN
    DELETE FROM channels_channelcount WHERE count_type IN ('LE', 'LS');
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

----------------------------------------------------------------------
-- Manages keeping track of the # of messages sent and received by a channel
----------------------------------------------------------------------
CREATE OR REPLACE FUNCTION temba_update_channelcount() RETURNS TRIGGER AS $$
DECLARE
  is_test boolean;
BEGIN
  -- Message being updated
  IF TG_OP = 'INSERT' THEN
    -- Return if there is no channel on this message
    IF NEW.channel_id IS NULL THEN
      RETURN NULL;
    END IF;

    -- Find out if this is a test contact
    SELECT contacts_contact.is_test INTO STRICT is_test FROM contacts_contact WHERE id=NEW.contact_id;

    -- Return if it is
    IF is_test THEN
      RETURN NULL;
    END IF;

    -- If this is an incoming message, without message type, then increment that count
    IF NEW.direction = 'I' THEN
      -- This is a voice message, increment that count
      IF NEW.msg_type = 'V' THEN
        PERFORM temba_insert_channelcount(NEW.channel_id, 'IV', NEW.created_on::date, 1);
      -- Otherwise, this is a normal message
      ELSE
        PERFORM temba_insert_channelcount(NEW.channel_id, 'IM', NEW.created_on::date, 1);
      END IF;

    -- This is an outgoing message
    ELSIF NEW.direction = 'O' THEN
      -- This is a voice message, increment that count
      IF NEW.msg_type = 'V' THEN
        PERFORM temba_insert_channelcount(NEW.channel_id, 'OV', NEW.created_on::date, 1);
      -- Otherwise, this is a normal message
      ELSE
        PERFORM temba_insert_channelcount(NEW.channel_id, 'OM', NEW.created_on::date, 1);
      END IF;

    END IF;

  -- Assert that updates aren't happening that we don't approve of
  ELSIF TG_OP = 'UPDATE' THEN
    -- If the direction is changing, blow up
    IF NEW.direction <> OLD.direction THEN
      RAISE EXCEPTION 'Cannot change direction on messages';
    END IF;

    -- Cannot move from IVR to Text, or IVR to Text
    IF (OLD.msg_type <> 'V' AND NEW.msg_type = 'V') OR (OLD.msg_type = 'V' AND NEW.msg_type <> 'V') THEN
      RAISE EXCEPTION 'Cannot change a message from voice to something else or vice versa';
    END IF;

    -- Cannot change created_on
    IF NEW.created_on <> OLD.created_on THEN
      RAISE EXCEPTION 'Cannot change created_on on messages';
    END IF;

  -- Table being cleared, reset all counts
  ELSIF TG_OP = 'TRUNCATE' THEN
    DELETE FROM channels_channel WHERE count_type IN ('IV', 'IM', 'OV', 'OM');
  END IF;

  RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Install INSERT, UPDATE and DELETE triggers
DROP TRIGGER IF EXISTS temba_channellog_update_channelcount on channels_channellog;
CREATE TRIGGER temba_channellog_update_channelcount
   AFTER INSERT OR UPDATE OF is_error, channel_id
   ON channels_channellog
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channellog_count();

-- Install TRUNCATE trigger
DROP TRIGGER IF EXISTS temba_channellog_truncate_channelcount on channels_channellog;
CREATE TRIGGER temba_channellog_truncate_channelcount
  AFTER TRUNCATE
  ON channels_channellog
  EXECUTE PROCEDURE temba_update_channellog_count();

-- Install INSERT, UPDATE and DELETE triggers
DROP TRIGGER IF EXISTS temba_msg_update_channelcount on msgs_msg;
CREATE TRIGGER temba_msg_update_channelcount
   AFTER INSERT OR UPDATE OF direction, msg_type, created_on
   ON msgs_msg
   FOR EACH ROW
   EXECUTE PROCEDURE temba_update_channelcount();

-- Install TRUNCATE trigger
DROP TRIGGER IF EXISTS temba_msg_clear_channelcount on msgs_msg;
CREATE TRIGGER temba_msg_clear_channelcount
  AFTER TRUNCATE
  ON msgs_msg
  EXECUTE PROCEDURE temba_update_channelcount();