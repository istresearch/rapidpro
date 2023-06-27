from datetime import timedelta

import iso8601

from django.utils import timezone

from temba.channels.models import Channel
from temba.contacts.models import URN, Contact, ContactGroup
from temba.flows.models import Flow, FlowRun, FlowSession
from temba.msgs.models import Msg
from temba.request_logs.models import HTTPLog
from temba.utils.text import slugify_with
from temba.utils.uuid import uuid4

# engine session statuses to db statuses
SESSION_STATUSES = {
    "waiting": FlowSession.STATUS_WAITING,
    "completed": FlowSession.STATUS_COMPLETED,
    "interrupted": FlowSession.STATUS_INTERRUPTED,
    "failed": FlowSession.STATUS_FAILED,
}

# engine run statuses to db statuses
RUN_STATUSES = {
    "active": FlowRun.STATUS_ACTIVE,
    "waiting": FlowRun.STATUS_WAITING,
    "completed": FlowRun.STATUS_COMPLETED,
    "interrupted": FlowRun.STATUS_INTERRUPTED,
    "failed": FlowRun.STATUS_FAILED,
}

# engine run statuses to db exit types
EXIT_TYPES = {
    "completed": FlowRun.EXIT_TYPE_COMPLETED,
    "interrupted": FlowRun.EXIT_TYPE_INTERRUPTED,
    "expired": FlowRun.EXIT_TYPE_EXPIRED,
    "failed": FlowRun.EXIT_TYPE_FAILED,
}

# engine contact statuses to db statuses
CONTACT_STATUSES = {
    "active": Contact.STATUS_ACTIVE,
    "blocked": Contact.STATUS_BLOCKED,
    "stopped": Contact.STATUS_STOPPED,
    "archived": Contact.STATUS_ARCHIVED,
}

PERSIST_EVENTS = {"msg_created", "msg_received"}


class MockSessionWriter:
    """
    Writes sessions and runs that should look almost like the real thing from mailroom/goflow
    """

    def __init__(self, contact, flow, start=None):
        self.org = contact.org
        self.contact = contact
        self.start = start
        self.session = None

        contact_def = {"uuid": str(self.contact.uuid), "name": self.contact.name, "language": self.contact.language}

        self.output = {
            "uuid": str(uuid4()),
            "type": Flow.GOFLOW_TYPES[flow.flow_type],
            "environment": self.org.as_environment_def(),
            "trigger": {
                "type": "manual",
                "flow": flow.as_export_ref(),
                "contact": contact_def,
                "triggered_on": self._now(),
            },
            "contact": contact_def,
            "runs": [
                {
                    "uuid": str(uuid4()),
                    "flow": flow.as_export_ref(),
                    "path": [],
                    "events": [],
                    "results": {},
                    "status": "active",
                    "created_on": self._now(),
                    "modified_on": self._now(),
                    "exited_on": None,
                }
            ],
            "status": "active",
        }

        self.current_run = self.output["runs"][0]
        self.current_node = None
        self.events = []

    def visit(self, node, exit_index=None):
        if self.current_node:
            from_exit = None
            if exit_index:
                from_exit = self.current_node["exits"][exit_index]
            else:
                # use first exit that points to this destination
                for e in self.current_node["exits"]:
                    if e.get("destination_uuid") == node["uuid"]:
                        from_exit = e
                        break

            assert from_exit, f"previous node {self.current_node['uuid']} has no exit to new node {node['uuid']}"

            self.current_run["path"][-1]["exit_uuid"] = from_exit["uuid"]

        self.current_run["path"].append({"uuid": str(uuid4()), "node_uuid": node["uuid"], "arrived_on": self._now()})
        self.current_run["modified_on"] = self._now()
        self.current_node = node
        return self

    def set_result(self, name, value, category, input):
        node_uuid = self.current_node["uuid"]

        self.current_run["results"][slugify_with(name)] = {
            "name": name,
            "value": value,
            "category": category,
            "node_uuid": node_uuid,
            "input": input,
            "created_on": self._now(),
        }
        self.current_run["modified_on"] = self._now()
        self._log_event(
            "run_result_changed", name=name, value=value, category=category, node_uuid=node_uuid, input=input
        )
        return self

    def add_contact_urn(self, scheme, path):
        urns = [str(u) for u in self.contact.get_urns()]
        urns.append(URN.from_parts(scheme, path))
        self._log_event("contact_urns_changed", urns=urns)
        return self

    def add_contact_groups(self, groups):
        self._log_event("contact_groups_changed", groups_added=[{"uuid": str(g.uuid), "name": g.name} for g in groups])
        return self

    def remove_contact_groups(self, groups):
        self._log_event(
            "contact_groups_changed", groups_removed=[{"uuid": str(g.uuid), "name": g.name} for g in groups]
        )
        return self

    def set_contact_status(self, status: str):
        self._log_event("contact_status_changed", status=status)
        return self

    def error(self, text):
        self._log_event("error", text=text)
        return self

    def send_msg(self, text, channel=None, attachments=()):
        msg = {
            "uuid": str(uuid4()),
            "urn": self.contact.get_urn().urn,
            "text": text,
            "channel": self._channel_ref(channel),
        }
        if attachments:
            msg["attachments"] = attachments

        self._log_event("msg_created", msg=msg)
        return self

    def send_email(self, to, subject, body):
        self._log_event("email_sent", to=to, subject=subject, body=body)
        return self

    def set_contact_field(self, field_key, field_name, value):
        self._log_event(
            "contact_field_changed",
            field={"key": field_key, "name": field_name},
            value={"text": value} if value else None,
        )
        return self

    def set_contact_language(self, language):
        self._log_event("contact_language_changed", language=language)
        return self

    def set_contact_name(self, name):
        self._log_event("contact_name_changed", name=name)
        return self

    def call_webhook(self, method, url, payload, status="success", status_code=200, response_body="{}"):
        path = "/" + url.rsplit("/", 1)[-1]

        self._log_event(
            "webhook_called",
            url=url,
            status=status,
            status_code=status_code,
            elapsed_ms=3,
            request=f"{method} {path} HTTP/1.1\r\n\r\n{payload}",
            response=f"HTTP/1.1 {status_code} OK\r\n\r\n{response_body}",
        )
        return self

    def transfer_airtime(self, sender, recipient, currency, desired_amount, actual_amount):
        self._log_event(
            "airtime_transferred",
            sender=sender,
            recipient=recipient,
            currency=currency,
            desired_amount=desired_amount,
            actual_amount=actual_amount,
        )
        return self

    def wait(self):
        self.output["status"] = "waiting"
        self.current_run["status"] = "waiting"
        self.current_run["modified_on"] = self._now()

        expires_on = None
        if self.output["type"] in ("messaging", "voice"):
            expires_on = (timezone.now() + timedelta(days=7)).isoformat()

        self._log_event("msg_wait", expires_on=expires_on)
        return self

    def resume(self, msg):
        assert self.output["status"] == "waiting", "can only resume a waiting session"
        assert self.current_run["status"] == "waiting", "can only resume a waiting run"

        msg_def = {"uuid": str(msg.uuid), "text": msg.text, "channel": self._channel_ref(msg.channel)}
        if msg.contact_urn:
            msg_def["urn"] = msg.contact_urn.urn

        self.output["wait"] = None
        self.output["status"] = "active"
        self.current_run["status"] = "active"
        self.current_run["modified_on"] = self._now()
        self._log_event("msg_received", msg=msg_def)
        return self

    def complete(self):
        self._exit("completed")
        return self

    def interrupt(self):
        self._exit("interrupted")
        return self

    def fail(self, text):
        self._log_event("failure", text=text)
        self._exit("failed")
        return self

    def save(self):
        assert self.output["status"] != "active", "active sessions never persisted to database"

        db_flow_types = {v: k for k, v in Flow.GOFLOW_TYPES.items()}

        # if we're starting a new session, interrupt any existing ones
        if not self.session:
            interrupted_on = self.output["trigger"]["triggered_on"]  # which would have happened at trigger time

            self.contact.sessions.filter(status=FlowSession.STATUS_WAITING).update(
                status=FlowSession.STATUS_INTERRUPTED, ended_on=timezone.now()
            )
            self.contact.runs.filter(status__in=(FlowRun.STATUS_ACTIVE, FlowRun.STATUS_WAITING)).update(
                status=FlowRun.STATUS_INTERRUPTED,
                modified_on=interrupted_on,
                exited_on=interrupted_on,
            )

        if self.output["status"] == "waiting":
            wait_event = None
            for evt in self.events:
                if evt["type"].endswith("_wait"):
                    wait_event = evt

            wait_started_on = timezone.now()
            wait_expires_on = iso8601.parse_date(wait_event["expires_on"]) if wait_event["expires_on"] else None
            wait_resume_on_expire = False  # this doesn't support sub-flows
        else:
            wait_started_on = None
            wait_expires_on = None
            wait_resume_on_expire = False

        # create or update session object itself
        if self.session:
            self.session.output = self.output
            self.session.status = SESSION_STATUSES[self.output["status"]]
            self.session.wait_started_on = wait_started_on
            self.session.wait_expires_on = wait_expires_on
            self.session.save(update_fields=("output", "status", "wait_started_on", "wait_expires_on"))
        else:
            self.session = FlowSession.objects.create(
                uuid=self.output["uuid"],
                org=self.org,
                contact=self.contact,
                session_type=db_flow_types[self.output["type"]],
                output=self.output,
                status=SESSION_STATUSES[self.output["status"]],
                wait_started_on=wait_started_on,
                wait_expires_on=wait_expires_on,
                wait_resume_on_expire=wait_resume_on_expire,
            )

        current_flow = None

        for i, run in enumerate(self.output["runs"]):
            if run["status"] == "waiting":
                current_flow = Flow.objects.get(uuid=run["flow"]["uuid"])

            db_state = dict(
                path=run["path"],
                results=run["results"],
                status=RUN_STATUSES[run["status"]],
                current_node_uuid=run["path"][-1]["node_uuid"] if run["path"] else None,
                modified_on=run["modified_on"],
                exited_on=run["exited_on"],
                responded=bool([e for e in run["events"] if e["type"] == "msg_received"]),
            )

            run_obj = FlowRun.objects.filter(uuid=run["uuid"]).first()
            if not run_obj:
                FlowRun.objects.create(
                    uuid=run["uuid"],
                    org=self.org,
                    start=self.start if i == 0 else None,
                    flow=Flow.objects.get(uuid=run["flow"]["uuid"]),
                    contact=self.contact,
                    session=self.session,
                    created_on=run["created_on"],
                    **db_state,
                )
            else:
                FlowRun.objects.filter(id=run_obj.id).update(**db_state)

        self.contact.current_flow = current_flow
        self.contact.modified_on = timezone.now()
        self.contact.save(update_fields=("current_flow", "modified_on"))

        self._handle_events()
        return self

    def _handle_events(self):
        for event in self.events:
            handle_fn = getattr(self, "_handle_" + event["type"], None)
            if handle_fn:
                handle_fn(event)
        self.events = []

    def _handle_msg_created(self, event):
        channel_ref = event["msg"].get("channel")
        attachments = event["msg"].get("attachments", [])

        Msg.objects.create(
            uuid=event["msg"]["uuid"],
            org=self.org,
            contact=self.contact,
            contact_urn=self.contact.get_urn(),
            channel=Channel.objects.get(uuid=channel_ref["uuid"]) if channel_ref else None,
            direction="O",
            text=event["msg"]["text"],
            attachments=attachments,
            created_on=event["created_on"],
            msg_type="F",
            status="S",
            sent_on=event["created_on"],
        )

    def _handle_contact_groups_changed(self, event):
        for group in event.get("groups_added", []):
            ContactGroup.objects.get(uuid=group["uuid"]).contacts.add(self.contact)

        for group in event.get("groups_removed", []):
            ContactGroup.objects.get(uuid=group["uuid"]).contacts.remove(self.contact)

    def _handle_contact_status_changed(self, event):
        self.contact.status = CONTACT_STATUSES[event["status"]]
        self.contact.modified_on = timezone.now()
        self.contact.save(update_fields=("status", "modified_on"))

    def _handle_webhook_called(self, event):
        HTTPLog.objects.create(
            org=self.org,
            log_type=HTTPLog.WEBHOOK_CALLED,
            url=event["url"],
            status_code=event["status_code"],
            is_error=event["status"] != "success",
            request=event["request"],
            response=event["response"],
            request_time=event["elapsed_ms"],
            num_retries=0,
        )

    @staticmethod
    def _now():
        return timezone.now().isoformat()

    @staticmethod
    def _channel_ref(channel):
        return {"uuid": str(channel.uuid), "name": channel.name} if channel else None

    def _log_event(self, _type, **kwargs):
        path = self.current_run["path"]
        step_uuid = path[-1]["uuid"] if path else None
        event = {"type": _type, "created_on": self._now(), "step_uuid": step_uuid, **kwargs}

        self.current_run["events"].append(event)
        self.events.append(event)

    def _exit(self, status):
        self.output["status"] = status

        for run in self.output["runs"]:
            run["status"] = status
            run["exited_on"] = self._now()
            run["modified_on"] = self._now()
