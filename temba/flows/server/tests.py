from unittest.mock import patch

from temba.channels.models import Channel
from temba.contacts.models import ContactGroup
from temba.msgs.models import Label
from temba.tests import MockResponse, TembaTest, matchers, skip_if_no_flowserver
from temba.values.constants import Value

from .assets import ChannelType, get_asset_type, get_asset_urls
from .client import FlowServerException
from .serialize import serialize_channel, serialize_field, serialize_flow, serialize_group, serialize_label

TEST_ASSETS_BASE = "http://localhost:8000/flow/assets/"


class AssetsTest(TembaTest):
    def test_get_asset_urls(self):
        self.assertEqual(
            get_asset_urls(self.org),
            {
                "channel": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/channel/"),
                "field": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/field/"),
                "flow": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/flow/"),
                "group": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/group/"),
                "label": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/label/"),
                "location_hierarchy": f"{TEST_ASSETS_BASE}{self.org.id}/1/location_hierarchy/",
                "resthook": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/resthook/"),
            },
        )

    def test_bundling(self):
        self.assertEqual(
            get_asset_type(ChannelType).bundle_set(self.org, simulator=True),
            {
                "type": "channel",
                "url": matchers.String(pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/channel/"),
                "content": [
                    {
                        "address": "+250785551212",
                        "country": "RW",
                        "name": "Test Channel",
                        "roles": ["send", "receive"],
                        "schemes": ["tel"],
                        "uuid": str(self.channel.uuid),
                    },
                    {
                        "address": "+18005551212",
                        "name": "Simulator Channel",
                        "roles": ["send"],
                        "schemes": ["tel"],
                        "uuid": "440099cf-200c-4d45-a8e7-4a564f4a0e8b",
                    },
                ],
            },
        )
        self.assertEqual(
            get_asset_type(ChannelType).bundle_item(self.org, uuid=self.channel.uuid),
            {
                "type": "channel",
                "url": matchers.String(
                    pattern=f"{TEST_ASSETS_BASE}{self.org.id}/\d+/channel/{str(self.channel.uuid)}/"
                ),
                "content": {
                    "address": "+250785551212",
                    "country": "RW",
                    "name": "Test Channel",
                    "roles": ["send", "receive"],
                    "schemes": ["tel"],
                    "uuid": str(self.channel.uuid),
                },
            },
        )


class SerializationTest(TembaTest):
    def test_serialize_field(self):
        gender = self.create_field("gender", "Gender", Value.TYPE_TEXT)
        age = self.create_field("age", "Age", Value.TYPE_NUMBER)

        self.assertEqual(serialize_field(gender), {"key": "gender", "name": "Gender", "value_type": "text"})
        self.assertEqual(serialize_field(age), {"key": "age", "name": "Age", "value_type": "number"})

    @skip_if_no_flowserver
    def test_serialize_flow(self):
        flow = self.get_flow("favorites")
        migrated_json = serialize_flow(flow)
        self.assertEqual(migrated_json["uuid"], str(flow.uuid))
        self.assertEqual(migrated_json["name"], flow.name)
        self.assertEqual(len(migrated_json["nodes"]), 9)

    def test_serialize_group(self):
        spammers = ContactGroup.create_static(self.org, self.admin, "Spammers")
        self.assertEqual(serialize_group(spammers), {"uuid": str(spammers.uuid), "name": "Spammers", "query": None})

    def test_serialize_label(self):
        spam = Label.get_or_create(self.org, self.admin, "Spam")
        self.assertEqual(serialize_label(spam), {"uuid": str(spam.uuid), "name": "Spam"})

    def test_serialize_channel(self):
        nexmo = Channel.create(
            self.org,
            self.admin,
            country="",
            channel_type="NX",
            name="Bulk",
            address="1234",
            parent=self.channel,
            config={Channel.CONFIG_SHORTCODE_MATCHING_PREFIXES: ["25078"]},
        )

        self.assertEqual(
            serialize_channel(nexmo),
            {
                "uuid": str(nexmo.uuid),
                "name": "Bulk",
                "address": "1234",
                "roles": ["send", "receive"],
                "schemes": ["tel"],
                "match_prefixes": ["25078"],
                "parent": {"uuid": str(self.channel.uuid), "name": "Test Channel"},
            },
        )

        self.assertEqual(
            serialize_channel(self.channel),
            {
                "uuid": str(self.channel.uuid),
                "name": "Test Channel",
                "address": "+250785551212",
                "roles": ["send", "receive"],
                "schemes": ["tel"],
                "country": "RW",
            },
        )


class ClientTest(TembaTest):
    @patch("requests.post")
    def test_request_failure(self, mock_post):
        mock_post.return_value = MockResponse(400, '{"errors":["Bad request", "Doh!"]}')

        flow = self.get_flow("color")

        with self.assertRaises(FlowServerException) as e:
            serialize_flow(flow)

        self.assertEqual(
            e.exception.as_json(),
            {"endpoint": "migrate", "request": matchers.Dict(), "response": {"errors": ["Bad request", "Doh!"]}},
        )
