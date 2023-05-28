import logging

from temba.mailroom.events import (
    _url_for_user,
    get_event_time,
    _msg_in,
    _msg_out,
    Event,
    ChannelEvent,
)
from temba.msgs.models import Msg
from temba.orgs.models import Org, User


logger = logging.getLogger()

def getHistoryContentFromMsg(org: Org, user: User, obj: Msg) -> dict:
    """
    Reconstructs an engine event from a msg instance. Properties which aren't part of regular events are prefixed
    with an underscore.
    """
    channel_log = obj.get_last_log()
    logs_url = _url_for_user(org, user, "channels.channellog_read", args=[channel_log.id]) if channel_log else None
    if channel_log and channel_log.is_error:
        logger.debug("channel log is_error", extra={
            'context': 'contact history',
            'response_status': channel_log.response_status,
            'desc': channel_log.description,
        })

    if obj.direction == Msg.DIRECTION_IN:
        return {
            "type": Event.TYPE_MSG_RECEIVED,
            "created_on": get_event_time(obj).isoformat(),
            "msg": _msg_in(obj),
            # additional properties
            "msg_type": obj.msg_type,
            "logs_url": logs_url,
            "channel_log": channel_log,
        }
    elif obj.broadcast and obj.broadcast.get_message_count() > 1:
        return {
            "type": Event.TYPE_BROADCAST_CREATED,
            "created_on": get_event_time(obj).isoformat(),
            "translations": obj.broadcast.text,
            "base_language": obj.broadcast.base_language,
            # additional properties
            "msg": _msg_out(obj),
            "status": obj.status,
            "recipient_count": obj.broadcast.get_message_count(),
            "logs_url": logs_url,
            "channel_log": channel_log,
        }
    else:
        msg_event = {
            "type": Event.TYPE_IVR_CREATED if obj.msg_type == Msg.TYPE_IVR else Event.TYPE_MSG_CREATED,
            "created_on": get_event_time(obj).isoformat(),
            "msg": _msg_out(obj),
            # additional properties
            "status": obj.status,
            "logs_url": logs_url,
            "channel_log": channel_log,
        }

        if obj.broadcast and obj.broadcast.created_by:
            user = obj.broadcast.created_by
            msg_event["msg"]["created_by"] = {
                "id": user.id,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "email": user.email,
            }

        return msg_event
    #endif
#enddef getHistoryContentFromMsg()

def getHistoryContentFromChannelEvent(org: Org, user: User, obj: ChannelEvent) -> dict:
    """
    Added channel as a key so we can show which scheme a call may have been received.
    """
    extra = obj.extra or {}
    return {
        "type": Event.TYPE_CHANNEL_EVENT,
        "created_on": get_event_time(obj).isoformat(),
        "channel_event_type": obj.event_type,
        "duration": extra.get("duration"),
        "channel": obj.channel,
    }
#enddef getHistoryContentFromChannelEvent
