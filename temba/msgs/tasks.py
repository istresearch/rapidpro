import logging
import time
from datetime import timedelta

from django_redis import get_redis_connection

from django.core.cache import cache
from django.utils import timezone

from celery.task import task

from temba.channels.models import CHANNEL_EVENT, ChannelEvent
from temba.contacts.models import STOP_CONTACT_EVENT, Contact
from temba.utils import analytics
from temba.utils.queues import Queue, complete_task, nonoverlapping_task, start_task

from .models import (
    FIRE_EVENT,
    HANDLE_EVENT_TASK,
    Broadcast,
    BroadcastMsgCount,
    ExportMessagesTask,
    LabelCount,
    Msg,
    SystemLabelCount,
)

logger = logging.getLogger(__name__)


def process_fire_events(fire_ids):
    from temba.campaigns.models import EventFire

    # every event fire in the batch will be for the same flow... but if the flow has been deleted then fires won't exist
    single_fire = EventFire.objects.filter(id__in=fire_ids).first()
    if not single_fire:  # pragma: no cover
        return

    flow = single_fire.event.flow

    # lock on the flow so we know non-one else is updating these event fires
    r = get_redis_connection()
    with r.lock("process_fire_events:%d" % flow.id, timeout=300):

        # only fetch fires that haven't been somehow already handled
        fires = list(EventFire.objects.filter(id__in=fire_ids, fired=None).prefetch_related("contact"))
        if fires:
            print("E[%s][%s] Batch firing %d events..." % (flow.org.name, flow.name, len(fires)))

            start = time.time()
            EventFire.batch_fire(fires, flow)

            print("E[%s][%s] Finished batch firing events in %.3f s" % (flow.org.name, flow.name, time.time() - start))


@task(track_started=True, name="send_broadcast")
def send_broadcast_task(broadcast_id, **kwargs):
    # get our broadcast
    from .models import Broadcast

    broadcast = Broadcast.objects.get(pk=broadcast_id)

    high_priority = broadcast.recipient_count == 1
    expressions_context = {} if kwargs.get("with_expressions", True) else None

    broadcast.send(high_priority=high_priority, expressions_context=expressions_context)


@task(track_started=True, name="send_to_flow_node")
def send_to_flow_node(org_id, user_id, text, **kwargs):
    from django.contrib.auth.models import User
    from temba.contacts.models import Contact
    from temba.orgs.models import Org
    from temba.flows.models import FlowRun

    org = Org.objects.get(pk=org_id)
    user = User.objects.get(pk=user_id)
    node_uuid = kwargs.get("s", None)

    runs = FlowRun.objects.filter(org=org, current_node_uuid=node_uuid, is_active=True)

    contact_ids = (
        Contact.objects.filter(org=org, is_blocked=False, is_stopped=False, is_active=True)
        .filter(id__in=runs.values_list("contact", flat=True))
        .values_list("id", flat=True)
    )

    broadcast = Broadcast.create(org, user, text, contact_ids=contact_ids)
    broadcast.send(expressions_context={})

    analytics.track(user.username, "temba.broadcast_created", dict(contacts=len(contact_ids), groups=0, urns=0))


@task(track_started=True, name="send_spam")
def send_spam(user_id, contact_id):  # pragma: no cover
    """
    Processses a single incoming message through our queue.
    """
    from django.contrib.auth.models import User
    from temba.contacts.models import Contact, TEL_SCHEME
    from temba.msgs.models import Broadcast

    contact = Contact.objects.get(pk=contact_id)
    user = User.objects.get(pk=user_id)
    channel = contact.org.get_send_channel(TEL_SCHEME)

    if not channel:  # pragma: no cover
        print("Sorry, no channel to be all spammy with")
        return

    long_text = (
        "Test Message #%d. The path of the righteous man is beset on all sides by the iniquities of the "
        "selfish and the tyranny of evil men. Blessed is your face."
    )

    # only trigger sync on the last one
    for idx in range(10):
        broadcast = Broadcast.create(contact.org, user, long_text % (idx + 1), contacts=[contact])
        broadcast.send(trigger_send=(idx == 149))


@task(track_started=True, name="fail_old_messages")
def fail_old_messages():  # pragma: needs cover
    Msg.fail_old_messages()


@nonoverlapping_task(track_started=True, name="collect_message_metrics_task", time_limit=900)
def collect_message_metrics_task():  # pragma: needs cover
    """
    Collects message metrics and sends them to our analytics.
    """
    from .models import INCOMING, OUTGOING, PENDING, QUEUED, ERRORED, INITIALIZING
    from temba.utils import analytics

    # current # of queued messages (excluding Android)
    count = (
        Msg.objects.filter(direction=OUTGOING, status=QUEUED)
        .exclude(channel=None)
        .exclude(topup=None)
        .exclude(channel__channel_type="A")
        .exclude(next_attempt__gte=timezone.now())
        .count()
    )
    analytics.gauge("temba.current_outgoing_queued", count)

    # current # of initializing messages (excluding Android)
    count = (
        Msg.objects.filter(direction=OUTGOING, status=INITIALIZING)
        .exclude(channel=None)
        .exclude(topup=None)
        .exclude(channel__channel_type="A")
        .count()
    )
    analytics.gauge("temba.current_outgoing_initializing", count)

    # current # of pending messages (excluding Android)
    count = (
        Msg.objects.filter(direction=OUTGOING, status=PENDING)
        .exclude(channel=None)
        .exclude(topup=None)
        .exclude(channel__channel_type="A")
        .count()
    )
    analytics.gauge("temba.current_outgoing_pending", count)

    # current # of errored messages (excluding Android)
    count = (
        Msg.objects.filter(direction=OUTGOING, status=ERRORED)
        .exclude(channel=None)
        .exclude(topup=None)
        .exclude(channel__channel_type="A")
        .count()
    )
    analytics.gauge("temba.current_outgoing_errored", count)

    # current # of android outgoing messages waiting to be sent
    count = (
        Msg.objects.filter(direction=OUTGOING, status__in=[PENDING, QUEUED], channel__channel_type="A")
        .exclude(channel=None)
        .exclude(topup=None)
        .count()
    )
    analytics.gauge("temba.current_outgoing_android", count)

    # current # of pending incoming messages older than a minute that haven't yet been handled
    minute_ago = timezone.now() - timedelta(minutes=1)
    count = (
        Msg.objects.filter(direction=INCOMING, status=PENDING, created_on__lte=minute_ago)
        .exclude(channel=None)
        .count()
    )
    analytics.gauge("temba.current_incoming_pending", count)

    # stuff into redis when we last run, we do this as a canary as to whether our tasks are falling behind or not running
    cache.set("last_cron", timezone.now())


@nonoverlapping_task(track_started=True, name="check_messages_task", time_limit=900)
def check_messages_task():  # pragma: needs cover
    """
    Checks to see if any of our aggregators have errored messages that need to be retried.
    Also takes care of flipping Contacts from Failed to Normal and back based on their status.
    """

    from temba.orgs.models import Org

    now = timezone.now()
    five_minutes_ago = now - timedelta(minutes=5)
    r = get_redis_connection()

    # for any org that sent messages in the past five minutes, check for pending messages
    for org in Org.objects.filter(msgs__created_on__gte=five_minutes_ago, flow_server_enabled=False).distinct():
        # more than 1,000 messages queued? don't do anything, wait for our queue to go down
        queued = r.zcard("send_message_task:%d" % org.id)
        if queued < 1000:
            org.trigger_send()

    # fire a few tasks in case we dropped one somewhere during a restart
    # (these will be no-ops if there is nothing to do)
    for i in range(100):
        handle_event_task.apply_async(queue=Queue.HANDLER)


@task(track_started=True, name="export_sms_task")
def export_messages_task(export_id):
    """
    Export messages to a file and e-mail a link to the user
    """
    ExportMessagesTask.objects.get(id=export_id).perform()


@task(track_started=True, name="handle_event_task", time_limit=180, soft_time_limit=120)
def handle_event_task():
    """
    Priority queue task that handles both event fires (when fired) and new incoming
    messages that need to be handled.

    Currently three types of events may be "popped" from our queue:
             msg - Which contains the id of the Msg to be processed
            fire - Which contains the id of the EventFire that needs to be fired
         timeout - Which contains a run that timed out and needs to be resumed
    stop_contact - Which contains the contact id to stop
    """
    # pop off the next task
    org_id, event_task = start_task(HANDLE_EVENT_TASK)

    # it is possible we have no message to send, if so, just return
    if not event_task:  # pragma: needs cover
        return

    try:
        if event_task["type"] == FIRE_EVENT:
            fire_ids = event_task.get("fires") if "fires" in event_task else [event_task.get("id")]
            process_fire_events(fire_ids)

        elif event_task["type"] == STOP_CONTACT_EVENT:
            contact = Contact.objects.get(id=event_task["contact_id"])
            contact.stop(contact.modified_by)

        elif event_task["type"] == CHANNEL_EVENT:
            event = ChannelEvent.objects.get(id=event_task["event_id"])
            event.handle()

        else:  # pragma: needs cover
            raise Exception("Unexpected event type: %s" % event_task)
    finally:
        complete_task(HANDLE_EVENT_TASK, org_id)


@nonoverlapping_task(track_started=True, name="squash_msgcounts", lock_timeout=7200)
def squash_msgcounts():
    SystemLabelCount.squash()
    LabelCount.squash()
    BroadcastMsgCount.squash()
