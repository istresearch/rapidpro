from uuid import uuid4

from django.conf import settings

from temba.channels.models import Channel
from temba.contacts.models import URN, Contact, ContactField, ContactGroup, ContactURN
from temba.values.constants import Value

from ..expressions import evaluate


class Action:
    """
    Base class for actions that can be added to an action set and executed during a flow run
    """

    TYPE = "type"
    UUID = "uuid"

    __action_mapping = None

    def __init__(self, uuid):
        self.uuid = uuid if uuid else str(uuid4())

    @classmethod
    def from_json(cls, org, json_obj):
        if not cls.__action_mapping:
            cls.__action_mapping = {
                ReplyAction.TYPE: ReplyAction,
                SendAction.TYPE: SendAction,
                AddToGroupAction.TYPE: AddToGroupAction,
                DeleteFromGroupAction.TYPE: DeleteFromGroupAction,
                AddLabelAction.TYPE: AddLabelAction,
                EmailAction.TYPE: EmailAction,
                SaveToContactAction.TYPE: SaveToContactAction,
                SetLanguageAction.TYPE: SetLanguageAction,
                SetChannelAction.TYPE: SetChannelAction,
                StartFlowAction.TYPE: StartFlowAction,
                SayAction.TYPE: SayAction,
                PlayAction.TYPE: PlayAction,
                TriggerFlowAction.TYPE: TriggerFlowAction,
            }

        action_type = json_obj.get(cls.TYPE)
        return cls.__action_mapping[action_type].from_json(org, json_obj)

    @classmethod
    def from_json_array(cls, org, json_arr):
        actions = []
        for inner in json_arr:
            action = Action.from_json(org, inner)
            if action:
                actions.append(action)
        return actions

    def execute(self, run, context, actionset_uuid, msg):  # pragma: no cover
        pass


class EmailAction(Action):
    """
    Sends an email to someone
    """

    TYPE = "email"
    EMAILS = "emails"
    SUBJECT = "subject"
    MESSAGE = "msg"

    def __init__(self, uuid, emails, subject, message):
        super().__init__(uuid)

        self.emails = emails
        self.subject = subject
        self.message = message

    @classmethod
    def from_json(cls, org, json_obj):
        emails = json_obj.get(EmailAction.EMAILS)
        message = json_obj.get(EmailAction.MESSAGE)
        subject = json_obj.get(EmailAction.SUBJECT)
        return cls(json_obj.get(cls.UUID), emails, subject, message)

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, emails=self.emails, subject=self.subject, msg=self.message)


class AddToGroupAction(Action):
    """
    Adds the user to a group
    """

    TYPE = "add_group"
    GROUP = "group"
    GROUPS = "groups"

    def __init__(self, uuid, groups):
        super().__init__(uuid)

        self.groups = groups

    @classmethod
    def from_json(cls, org, json_obj):
        return cls(json_obj.get(cls.UUID), cls.get_groups(org, json_obj))

    @classmethod
    def get_groups(cls, org, json_obj):

        # for backwards compatibility
        group_data = json_obj.get(AddToGroupAction.GROUP, None)
        if not group_data:
            group_data = json_obj.get(AddToGroupAction.GROUPS)
        else:
            group_data = [group_data]

        groups = []

        for g in group_data:
            if isinstance(g, dict):
                group_uuid = g.get("uuid", None)
                group_name = g.get("name")

                group = ContactGroup.get_or_create(org, org.created_by, group_name, uuid=group_uuid)
                groups.append(group)
            else:
                if g and g[0] == "@":
                    groups.append(g)
                else:  # pragma: needs cover
                    group = ContactGroup.get_user_group_by_name(org, g)
                    if group:
                        groups.append(group)
                    else:
                        groups.append(ContactGroup.create_static(org, org.get_user(), g))
        return groups

    def as_json(self):
        groups = []
        for g in self.groups:
            if isinstance(g, ContactGroup):
                groups.append(dict(uuid=g.uuid, name=g.name))
            else:
                groups.append(g)

        return dict(type=self.get_type(), uuid=self.uuid, groups=groups)

    def get_type(self):
        return AddToGroupAction.TYPE

    def execute(self, run, context, actionset_uuid, msg):  # pragma: no cover
        from temba.flows.models import get_flow_user

        contact = run.contact
        add = AddToGroupAction.TYPE == self.get_type()
        user = get_flow_user(run.org)

        if contact:
            for group in self.groups:
                if not isinstance(group, ContactGroup):
                    (value, errors) = evaluate(group, context, org=run.flow.org)
                    group = None

                    if not errors:
                        group = ContactGroup.get_user_group_by_name(contact.org, value)

                if group:
                    if group.is_dynamic:
                        continue

                    group.org = run.org
                    group.update_contacts(user, [contact], add)

        return []


class DeleteFromGroupAction(AddToGroupAction):
    """
    Removes the user from a group
    """

    TYPE = "del_group"

    def get_type(self):
        return DeleteFromGroupAction.TYPE

    def as_json(self):
        groups = []
        for g in self.groups:
            if isinstance(g, ContactGroup):
                groups.append(dict(uuid=g.uuid, name=g.name))
            else:
                groups.append(g)

        return dict(type=self.get_type(), uuid=self.uuid, groups=groups)

    @classmethod
    def from_json(cls, org, json_obj):
        return cls(json_obj.get(cls.UUID), cls.get_groups(org, json_obj))

    def execute(self, run, context, actionset, msg):  # pragma: no cover
        from temba.flows.models import get_flow_user

        if len(self.groups) == 0:
            contact = run.contact
            user = get_flow_user(run.org)
            if contact:
                # remove from all active and inactive user-defined, static groups
                for group in ContactGroup.user_groups.filter(
                    org=contact.org, group_type=ContactGroup.TYPE_USER_DEFINED, query__isnull=True
                ):
                    group.update_contacts(user, [contact], False)
            return []
        return AddToGroupAction.execute(self, run, context, actionset, msg)


class AddLabelAction(Action):
    """
    Add a label to the incoming message
    """

    TYPE = "add_label"
    LABELS = "labels"

    def __init__(self, uuid, labels):
        super().__init__(uuid)

        self.labels = labels

    @classmethod
    def from_json(cls, org, json_obj):
        from temba.msgs.models import Label

        labels_data = json_obj.get(cls.LABELS)

        labels = []
        for label_data in labels_data:
            if isinstance(label_data, dict):
                label_uuid = label_data.get("uuid", None)
                label_name = label_data.get("name")

                if label_uuid and Label.label_objects.filter(org=org, uuid=label_uuid).first():
                    label = Label.label_objects.filter(org=org, uuid=label_uuid).first()
                    if label:
                        labels.append(label)
                else:  # pragma: needs cover
                    labels.append(Label.get_or_create(org, org.get_user(), label_name))

            elif isinstance(label_data, str):
                if label_data and label_data[0] == "@":
                    # label name is a variable substitution
                    labels.append(label_data)
                else:  # pragma: needs cover
                    labels.append(Label.get_or_create(org, org.get_user(), label_data))
            else:  # pragma: needs cover
                raise ValueError("Label data must be a dict or string")

        return cls(json_obj.get(cls.UUID), labels)

    def as_json(self):
        from temba.msgs.models import Label

        labels = []
        for action_label in self.labels:
            if isinstance(action_label, Label):
                labels.append(dict(uuid=action_label.uuid, name=action_label.name))
            else:
                labels.append(action_label)

        return dict(type=self.TYPE, uuid=self.uuid, labels=labels)


class SayAction(Action):
    """
    Voice action for reading some text to a user
    """

    TYPE = "say"
    MESSAGE = "msg"
    RECORDING = "recording"

    def __init__(self, uuid, msg, recording):
        super().__init__(uuid)

        self.msg = msg
        self.recording = recording

    @classmethod
    def from_json(cls, org, json_obj):
        return cls(json_obj.get(cls.UUID), json_obj.get(cls.MESSAGE), json_obj.get(cls.RECORDING))

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, msg=self.msg, recording=self.recording)


class PlayAction(Action):
    """
    Voice action for reading some text to a user
    """

    TYPE = "play"
    URL = "url"

    def __init__(self, uuid, url):
        super().__init__(uuid)

        self.url = url

    @classmethod
    def from_json(cls, org, json_obj):
        return cls(json_obj.get(cls.UUID), json_obj.get(cls.URL))

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, url=self.url)


class ReplyAction(Action):
    """
    Simple action for sending back a message
    """

    TYPE = "reply"
    MESSAGE = "msg"
    MSG_TYPE = None
    MEDIA = "media"
    SEND_ALL = "send_all"
    QUICK_REPLIES = "quick_replies"

    def __init__(self, uuid, msg=None, media=None, quick_replies=None, send_all=False):
        super().__init__(uuid)

        self.msg = msg
        self.media = media if media else {}
        self.send_all = send_all
        self.quick_replies = quick_replies if quick_replies else []

    @classmethod
    def from_json(cls, org, json_obj):
        from temba.flows.models import FlowException

        # assert we have some kind of message in this reply
        msg = json_obj.get(cls.MESSAGE)
        if isinstance(msg, dict):
            if not msg:
                raise FlowException("Invalid reply action, empty message dict")

            if not any([v for v in msg.values()]):
                raise FlowException("Invalid reply action, missing at least one message")
        elif not msg:
            raise FlowException("Invalid reply action, no message")

        return cls(
            json_obj.get(cls.UUID),
            msg=json_obj.get(cls.MESSAGE),
            media=json_obj.get(cls.MEDIA, None),
            quick_replies=json_obj.get(cls.QUICK_REPLIES),
            send_all=json_obj.get(cls.SEND_ALL, False),
        )

    def as_json(self):
        return dict(
            type=self.TYPE,
            uuid=self.uuid,
            msg=self.msg,
            media=self.media,
            quick_replies=self.quick_replies,
            send_all=self.send_all,
        )

    @staticmethod
    def get_translated_quick_replies(metadata, run):  # pragma: no cover
        """
        Gets the appropriate metadata translation for the given contact
        """
        from ..engine import get_localized_text

        language_metadata = []
        for item in metadata:
            text = get_localized_text(run.flow, text_translations=item, contact=run.contact)
            language_metadata.append(text)

        return language_metadata

    @staticmethod
    def get_session_responded(run):
        current_run = run
        while current_run and current_run.contact_id == run.contact_id:
            if current_run.responded:
                return True
            current_run = current_run.parent
        return False

    def execute(self, run, context, actionset_uuid, msg):  # pragma: no cover
        from temba.flows.models import get_flow_user
        from ..engine import get_localized_text

        replies = []

        if self.msg or self.media:
            user = get_flow_user(run.org)

            text = ""
            if self.msg:
                text = get_localized_text(run.flow, self.msg, run.contact)

            quick_replies = []
            if self.quick_replies:
                quick_replies = ReplyAction.get_translated_quick_replies(self.quick_replies, run)

            attachments = None
            if self.media:
                # localize our media attachment
                media_type, media_url = get_localized_text(run.flow, self.media, run.contact).split(":", 1)

                # if we have a localized media, create the url
                if media_url and len(media_type.split("/")) > 1:
                    abs_url = f"{settings.STORAGE_URL}/{media_url}"
                    attachments = [f"{media_type}:{abs_url}"]
                else:
                    attachments = [f"{media_type}:{media_url}"]

            if msg and msg.id:
                replies = msg.reply(
                    text,
                    user,
                    trigger_send=False,
                    expressions_context=context,
                    connection=run.connection,
                    msg_type=self.MSG_TYPE,
                    quick_replies=quick_replies,
                    attachments=attachments,
                    send_all=self.send_all,
                    sent_on=None,
                )
            else:
                # if our run has been responded to or any of our parent runs have
                # been responded to consider us interactive with high priority
                high_priority = self.get_session_responded(run)
                replies = run.contact.send(
                    text,
                    user,
                    trigger_send=False,
                    expressions_context=context,
                    connection=run.connection,
                    msg_type=self.MSG_TYPE,
                    attachments=attachments,
                    quick_replies=quick_replies,
                    sent_on=None,
                    all_urns=self.send_all,
                    high_priority=high_priority,
                )
        return replies


class VariableContactAction(Action):  # pragma: no cover
    """
    Base action that resolves variables into contacts. Used for actions that take
    SendAction, TriggerAction, etc
    """

    CONTACTS = "contacts"
    GROUPS = "groups"
    VARIABLES = "variables"
    PHONE = "phone"
    PATH = "path"
    SCHEME = "scheme"
    URNS = "urns"
    NAME = "name"
    ID = "id"

    def __init__(self, uuid, groups, contacts, variables):
        super().__init__(uuid)

        self.groups = groups
        self.contacts = contacts
        self.variables = variables

    @classmethod
    def parse_groups(cls, org, json_obj):
        # we actually instantiate our contacts here
        groups = []
        for group_data in json_obj.get(VariableContactAction.GROUPS):
            group_uuid = group_data.get(VariableContactAction.UUID, None)
            group_name = group_data.get(VariableContactAction.NAME)

            # flows from when true deletion was allowed need this
            if not group_name:
                group_name = "Missing"

            group = ContactGroup.get_or_create(org, org.get_user(), group_name, uuid=group_uuid)
            groups.append(group)

        return groups

    @classmethod
    def parse_contacts(cls, org, json_obj):
        contacts = []
        for contact in json_obj.get(VariableContactAction.CONTACTS):
            name = contact.get(VariableContactAction.NAME, None)
            phone = contact.get(VariableContactAction.PHONE, None)
            contact_uuid = contact.get(VariableContactAction.UUID, None)

            urns = []
            for urn in contact.get(VariableContactAction.URNS, []):
                scheme = urn.get(VariableContactAction.SCHEME)
                path = urn.get(VariableContactAction.PATH)

                if scheme and path:
                    urns.append(URN.from_parts(scheme, path))

            if phone:  # pragma: needs cover
                urns.append(URN.from_tel(phone))

            contact = Contact.objects.filter(uuid=contact_uuid, org=org).first()

            if not contact:
                contact = Contact.get_or_create_by_urns(org, org.created_by, name=None, urns=urns)

                # if they don't have a name use the one in our action
                if name and not contact.name:  # pragma: needs cover
                    contact.name = name
                    contact.save(update_fields=["name"], handle_update=True)

            if contact:
                contacts.append(contact)

        return contacts

    @classmethod
    def parse_variables(cls, org, json_obj):
        variables = []
        if VariableContactAction.VARIABLES in json_obj:
            variables = list(_.get(VariableContactAction.ID) for _ in json_obj.get(VariableContactAction.VARIABLES))
        return variables


class TriggerFlowAction(VariableContactAction):
    """
    Action that starts a set of contacts down another flow
    """

    TYPE = "trigger-flow"

    def __init__(self, uuid, flow, groups, contacts, variables):
        super().__init__(uuid, groups, contacts, variables)

        self.flow = flow

    @classmethod
    def from_json(cls, org, json_obj):
        from temba.flows.models import Flow

        flow_json = json_obj.get("flow")
        flow_uuid = flow_json.get("uuid")
        flow = Flow.objects.filter(org=org, is_active=True, is_archived=False, uuid=flow_uuid).first()

        # it is possible our flow got deleted
        if not flow:
            return None

        groups = VariableContactAction.parse_groups(org, json_obj)
        contacts = VariableContactAction.parse_contacts(org, json_obj)
        variables = VariableContactAction.parse_variables(org, json_obj)

        return cls(json_obj.get(cls.UUID), flow, groups, contacts, variables)

    def as_json(self):
        contact_ids = [dict(uuid=_.uuid, name=_.name) for _ in self.contacts]
        group_ids = [dict(uuid=_.uuid, name=_.name) for _ in self.groups]
        variables = [dict(id=_) for _ in self.variables]

        return dict(
            type=self.TYPE,
            uuid=self.uuid,
            flow=dict(uuid=self.flow.uuid, name=self.flow.name),
            contacts=contact_ids,
            groups=group_ids,
            variables=variables,
        )


class SetLanguageAction(Action):
    """
    Action that sets the language for a contact
    """

    TYPE = "lang"
    LANG = "lang"
    NAME = "name"

    def __init__(self, uuid, lang, name):
        super().__init__(uuid)

        self.lang = lang
        self.name = name

    @classmethod
    def from_json(cls, org, json_obj):
        return cls(json_obj.get(cls.UUID), json_obj.get(cls.LANG), json_obj.get(cls.NAME))

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, lang=self.lang, name=self.name)


class StartFlowAction(Action):
    """
    Action that starts the contact into another flow
    """

    TYPE = "flow"
    FLOW = "flow"
    NAME = "name"

    def __init__(self, uuid, flow):
        super().__init__(uuid)

        self.flow = flow

    @classmethod
    def from_json(cls, org, json_obj):
        from temba.flows.models import Flow

        flow_obj = json_obj.get(cls.FLOW)
        flow_uuid = flow_obj.get("uuid")

        flow = Flow.objects.filter(org=org, is_active=True, is_archived=False, uuid=flow_uuid).first()

        # it is possible our flow got deleted
        if not flow:
            return None
        else:
            return cls(json_obj.get(cls.UUID), flow)

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, flow=dict(uuid=self.flow.uuid, name=self.flow.name))

    def execute(self, run, context, actionset_uuid, msg, started_flows):  # pragma: no cover
        from ..engine import flow_start

        msgs = []

        # our extra will be our flow variables in our message context
        extra = context.get("extra", dict())

        child_runs = flow_start(
            self.flow,
            [],
            [run.contact],
            started_flows=started_flows,
            restart_participants=True,
            extra=extra,
            parent_run=run,
        )
        for run in child_runs:
            for msg in run.start_msgs:
                msg.from_other_run = True
                msgs.append(msg)

        return msgs


class SaveToContactAction(Action):
    """
    Action to save a variable substitution to a field on a contact
    """

    TYPE = "save"
    FIELD = "field"
    LABEL = "label"
    VALUE = "value"

    def __init__(self, uuid, label, field, value):
        super().__init__(uuid)

        self.label = label
        self.field = field
        self.value = value

    @classmethod
    def get_label(cls, org, field, label=None):
        from temba.flows.models import get_flow_user

        # make sure this field exists
        if field == "name":
            label = "Contact Name"
        elif field == "first_name":
            label = "First Name"
        elif field == "tel_e164":
            label = "Phone Number"
        elif field in ContactURN.CONTEXT_KEYS_TO_SCHEME.keys():
            label = str(ContactURN.CONTEXT_KEYS_TO_LABEL[field])
        else:
            contact_field = ContactField.user_fields.filter(org=org, key=field).first()

            if not contact_field:
                contact_field = ContactField.get_or_create(org, get_flow_user(org), field, label)

            label = contact_field.label

        return label

    @classmethod
    def from_json(cls, org, json_obj):
        # they are creating a new field
        label = json_obj.get(cls.LABEL)
        field = json_obj.get(cls.FIELD)
        value = json_obj.get(cls.VALUE)

        if label and label.startswith("[_NEW_]"):
            label = label[7:]

        # create our contact field if necessary
        if not field:
            field = ContactField.make_key(label)

        # look up our label
        label = cls.get_label(org, field, label)

        return cls(json_obj.get(cls.UUID), label, field, value)

    def as_json(self):
        return dict(type=self.TYPE, uuid=self.uuid, label=self.label, field=self.field, value=self.value)

    def execute(self, run, context, actionset_uuid, msg):  # pragma: no cover
        from temba.flows.models import get_flow_user

        # evaluate our value
        contact = run.contact
        user = get_flow_user(run.org)
        (value, errors) = evaluate(self.value, context, org=run.flow.org)

        value = value.strip()

        if self.field == "name":
            new_value = value[:128]
            contact.name = new_value
            contact.modified_by = user
            contact.save(update_fields=("name", "modified_by", "modified_on"), handle_update=True)

        elif self.field == "first_name":
            new_value = value[:128]
            contact.set_first_name(new_value)
            contact.modified_by = user
            contact.save(update_fields=("name", "modified_by", "modified_on"), handle_update=True)

        elif self.field in ContactURN.CONTEXT_KEYS_TO_SCHEME.keys():
            new_value = value[:128]

            # add in our new urn number
            scheme = ContactURN.CONTEXT_KEYS_TO_SCHEME[self.field]

            # trim off '@' for twitter handles
            if self.field == "twitter":  # pragma: needs cover
                if len(new_value) > 0:
                    if new_value[0] == "@":
                        new_value = new_value[1:]

            # only valid urns get added, sorry
            new_urn = None
            if new_value:
                new_urn = URN.normalize(URN.from_parts(scheme, new_value))
                if not URN.validate(new_urn, contact.org.get_country_code()):  # pragma: no cover
                    new_urn = False

            if new_urn:
                urns = [str(urn) for urn in contact.urns.all()]
                urns += [new_urn]
                contact.update_urns(user, urns)

        else:
            new_value = value[: Value.MAX_VALUE_LEN]
            contact.set_field(user, self.field, new_value)

        return []


class SetChannelAction(Action):
    """
    Action which sets the preferred channel to use for this Contact. If the contact has no URNs that match
    the Channel being set then this is a no-op.
    """

    TYPE = "channel"
    CHANNEL = "channel"
    NAME = "name"

    def __init__(self, uuid, channel):
        super().__init__(uuid)

        self.channel = channel

    @classmethod
    def from_json(cls, org, json_obj):
        channel_uuid = json_obj.get(SetChannelAction.CHANNEL)

        if channel_uuid:
            channel = Channel.objects.filter(org=org, is_active=True, uuid=channel_uuid).first()
        else:  # pragma: needs cover
            channel = None
        return cls(json_obj.get(cls.UUID), channel)

    def as_json(self):
        channel_uuid = self.channel.uuid if self.channel else None
        channel_name = (
            "%s: %s" % (self.channel.get_channel_type_display(), self.channel.get_address_display())
            if self.channel
            else None
        )
        return dict(type=self.TYPE, uuid=self.uuid, channel=channel_uuid, name=channel_name)


class SendAction(VariableContactAction):
    """
    Action which sends a message to a specified set of contacts and groups.
    """

    TYPE = "send"
    MESSAGE = "msg"
    MEDIA = "media"

    def __init__(self, uuid, msg, groups, contacts, variables, media=None):
        super().__init__(uuid, groups, contacts, variables)

        self.msg = msg
        self.media = media if media else {}

    @classmethod
    def from_json(cls, org, json_obj):
        groups = VariableContactAction.parse_groups(org, json_obj)
        contacts = VariableContactAction.parse_contacts(org, json_obj)
        variables = VariableContactAction.parse_variables(org, json_obj)

        return cls(
            json_obj.get(cls.UUID),
            json_obj.get(cls.MESSAGE),
            groups,
            contacts,
            variables,
            json_obj.get(cls.MEDIA, None),
        )

    def as_json(self):
        contact_ids = [dict(uuid=_.uuid) for _ in self.contacts]
        group_ids = [dict(uuid=_.uuid, name=_.name) for _ in self.groups]
        variables = [dict(id=_) for _ in self.variables]

        return dict(
            type=self.TYPE,
            uuid=self.uuid,
            msg=self.msg,
            contacts=contact_ids,
            groups=group_ids,
            variables=variables,
            media=self.media,
        )
