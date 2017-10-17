from __future__ import unicode_literals, absolute_import, print_function

import json
import requests
import six

from django.conf import settings
from django.db.models import Prefetch
from django.utils.timezone import now
from mptt.utils import get_cached_trees
from temba.utils import datetime_to_str
from temba.values.models import Value


VALUE_TYPE_NAMES = {c[0]: c[2] for c in Value.TYPE_CONFIG}


def serialize_flow(flow, strip_ui=True):
    """
    Migrates the given flow, returning None if the flow or any of its dependencies can't be run in
    goflow because of unsupported features.
    """
    flow_def = flow.as_json(expand_contacts=True)

    migrated_flow_def = get_client().migrate({'flows': [flow_def]})[0]

    if strip_ui:
        del migrated_flow_def['_ui']

    return migrated_flow_def


def serialize_channel(channel):
    return {
        'uuid': str(channel.uuid),
        'name': six.text_type(channel.get_name()),
        'type': channel.channel_type,
        'address': channel.address
    }


def serialize_field(field):
    return {'key': field.key, 'label': field.label, 'value_type': VALUE_TYPE_NAMES[field.value_type]}


def serialize_group(group):
    return {'uuid': str(group.uuid), 'name': group.name, 'query': group.query}


def serialize_label(label):
    return {'uuid': str(label.uuid), 'name': label.name}


def serialize_location_hierarchy(country, aliases_from_org):
    """
    Serializes a country as a location hierarchy, e.g.
    {
        "id": "34354",
        "name": "Rwanda",
        "children": [
            {
                "id": "23452561"
                "name": "Kigali City",
                "aliases": ["Kigali", "Kigari"],
                "children": [
                    ...
                ]
            }
        ]
    }
    """
    queryset = country.get_descendants(include_self=True)

    if aliases_from_org:
        from temba.locations.models import BoundaryAlias

        queryset = queryset.prefetch_related(
            Prefetch('aliases', queryset=BoundaryAlias.objects.filter(org=aliases_from_org)),
        )

    def _serialize_node(node):
        rendered = {'name': node.name}

        if aliases_from_org:
            rendered['aliases'] = [a.name for a in node.aliases.all()]

        children = node.get_children()
        if children:
            rendered['children'] = []
            for child in node.get_children():
                rendered['children'].append(_serialize_node(child))
        return rendered

    return [_serialize_node(node) for node in get_cached_trees(queryset)][0]


class RequestBuilder(object):
    def __init__(self, client, asset_timestamp):
        self.client = client
        self.asset_timestamp = asset_timestamp
        self.request = {'assets': [], 'events': []}

    def include_channel(self, channel):
        self.request['assets'].append({
            'type': "channel",
            'url': get_assets_url(channel.org, self.asset_timestamp, 'channel', str(channel.uuid)),
            'content': serialize_channel(channel)
        })
        return self

    def include_fields(self, org):
        from temba.contacts.models import ContactField

        self.request['assets'].append({
            'type': "field",
            'url': get_assets_url(org, self.asset_timestamp, 'field'),
            'content': [serialize_field(f) for f in ContactField.objects.filter(org=org, is_active=True)],
            'is_set': True
        })
        return self

    def include_flow(self, flow):
        self.request['assets'].append({
            'type': "flow",
            'url': get_assets_url(flow.org, self.asset_timestamp, 'flow', str(flow.uuid)),
            'content': serialize_flow(flow)
        })
        return self

    def include_groups(self, org):
        from temba.contacts.models import ContactGroup

        self.request['assets'].append({
            'type': "group",
            'url': get_assets_url(org, self.asset_timestamp, 'group'),
            'content': [serialize_group(g) for g in ContactGroup.get_user_groups(org)],
            'is_set': True
        })
        return self

    def include_labels(self, org):
        from temba.msgs.models import Label

        self.request['assets'].append({
            'type': "label",
            'url': get_assets_url(org, self.asset_timestamp, 'label'),
            'content': [serialize_label(l) for l in Label.label_objects.filter(org=org, is_active=True)],
            'is_set': True
        })
        return self

    def include_country(self, org):
        self.request['assets'].append({
            'type': "location_hierarchy",
            'url': get_assets_url(org, self.asset_timestamp, 'location_hierarchy'),
            'content': serialize_location_hierarchy(org.country, org)
        })
        return self

    def set_environment(self, org):
        languages = [org.primary_language.iso_code] if org.primary_language else []

        self.request['events'].append({
            'type': "set_environment",
            'created_on': datetime_to_str(now()),
            'date_format': "dd-MM-yyyy" if org.date_format == 'D' else "MM-dd-yyyy",
            'time_format': "hh:mm",
            'timezone': six.text_type(org.timezone),
            'languages': languages
        })
        return self

    def set_contact(self, contact):
        from temba.contacts.models import Contact
        from temba.msgs.models import Msg
        from temba.values.models import Value

        org_fields = {f.id: f for f in contact.org.contactfields.filter(is_active=True)}
        values = Value.objects.filter(contact=contact, contact_field_id__in=org_fields.keys())
        field_values = {}
        for v in values:
            field = org_fields[v.contact_field_id]
            field_values[field.key] = {
                'value': Contact.serialize_field_value(field, v, use_location_names=False),
                'created_on': datetime_to_str(v.created_on),
            }

        _contact, contact_urn = Msg.resolve_recipient(contact.org, None, contact, None)

        event = {
            'type': "set_contact",
            'created_on': datetime_to_str(now()),
            'contact': {
                'uuid': contact.uuid,
                'name': contact.name,
                'urns': [urn.urn for urn in contact.urns.all()],
                'group_uuids': [group.uuid for group in contact.user_groups.all()],
                'timezone': "UTC",
                'language': contact.language,
                'fields': field_values
            }
        }

        # only populate channel if this contact can actually be reached (ie, has a URN)
        if contact_urn:
            channel = contact.org.get_send_channel(contact_urn=contact_urn)
            if channel:
                event['contact']['channel_uuid'] = channel.uuid

        self.request['events'].append(event)
        return self

    def set_extra(self, extra):
        self.request['events'].append({
            'type': "set_extra",
            'created_on': datetime_to_str(now()),
            'extra': extra
        })
        return self

    def msg_received(self, msg):
        event = {
            'type': "msg_received",
            'created_on': datetime_to_str(msg.created_on),
            'msg_uuid': str(msg.uuid),
            'text': msg.text,
            'contact_uuid': str(msg.contact.uuid),

        }
        if msg.contact_urn:
            event['urn'] = msg.contact_urn.urn
        if msg.channel:
            event['channel_uuid'] = str(msg.channel.uuid)
        if msg.attachments:
            event['attachments'] = msg.attachments

        self.request['events'].append(event)
        return self

    def run_expired(self, run):
        self.request['events'].append({
            'type': "run_expired",
            'created_on': datetime_to_str(run.exited_on),
            'run_uuid': str(run.uuid),
        })
        return self

    def asset_urls(self, org):
        asset_urls = {
            'channel': get_assets_url(org, self.asset_timestamp, 'channel'),
            'field': get_assets_url(org, self.asset_timestamp, 'field'),
            'flow': get_assets_url(org, self.asset_timestamp, 'flow'),
            'group': get_assets_url(org, self.asset_timestamp, 'group'),
            'label': get_assets_url(org, self.asset_timestamp, 'label'),
        }

        if org.country_id:
            asset_urls['location_hierarchy'] = get_assets_url(org, self.asset_timestamp, 'location_hierarchy')

        self.request['asset_urls'] = asset_urls
        return self

    def start(self, flow):
        self.request['trigger'] = {
            'type': 'manual',
            'flow': {'uuid': str(flow.uuid), 'name': flow.name},
            'triggered_on': datetime_to_str(now())
        }

        return self.client.start(self.request)

    def resume(self, session):
        self.request['session'] = session

        return self.client.resume(self.request)


class Output(object):
    class LogEntry(object):
        def __init__(self, step_uuid, action_uuid, event):
            self.step_uuid = step_uuid
            self.action_uuid = action_uuid
            self.event = event

        @classmethod
        def from_json(cls, entry_json):
            return cls(entry_json.get('step_uuid'), entry_json.get('action_uuid'), entry_json['event'])

    def __init__(self, session, log):
        self.session = session
        self.log = log

    @classmethod
    def from_json(cls, output_json):
        return cls(output_json['session'], [Output.LogEntry.from_json(e) for e in output_json.get('log', [])])


class FlowServerException(Exception):
    pass


class FlowServerClient:
    """
    Basic client for GoFlow's flow server
    """
    def __init__(self, base_url, debug=False):
        self.base_url = base_url
        self.debug = debug

    def request_builder(self, asset_timestamp):
        return RequestBuilder(self, asset_timestamp)

    def start(self, flow_start):
        return Output.from_json(self._request('start', flow_start))

    def resume(self, flow_resume):
        return Output.from_json(self._request('resume', flow_resume))

    def migrate(self, flow_migrate):
        return self._request('migrate', flow_migrate)

    def _request(self, endpoint, payload):
        if self.debug:
            print('[GOFLOW]=============== %s request ===============' % endpoint)
            print(json.dumps(payload, indent=2))
            print('[GOFLOW]=============== /%s request ===============' % endpoint)

        response = requests.post("%s/flow/%s" % (self.base_url, endpoint), json=payload)
        resp_json = response.json()

        if self.debug:
            print('[GOFLOW]=============== %s response ===============' % endpoint)
            print(json.dumps(resp_json, indent=2))
            print('[GOFLOW]=============== /%s response ===============' % endpoint)

        if 400 <= response.status_code < 500:
            errors = "\n".join(resp_json['errors'])
            raise FlowServerException("Invalid request: " + errors)

        response.raise_for_status()

        return resp_json


def get_assets_url(org, timestamp, asset_type=None, asset_uuid=None):
    if settings.TESTING:
        url = 'http://localhost:8000/flow_assets/%d/%d' % (org.id, timestamp)
    else:
        url = 'https://%s/flow_assets/%d/%d' % (settings.HOSTNAME, org.id, timestamp)

    if asset_type:
        url = url + '/' + asset_type
    if asset_uuid:
        url = url + '/' + asset_uuid
    return url


def get_client():
    return FlowServerClient(settings.FLOW_SERVER_URL, settings.FLOW_SERVER_DEBUG)
