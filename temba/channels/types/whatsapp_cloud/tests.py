import json
from unittest.mock import call, patch

from requests import RequestException

from django.test import override_settings
from django.urls import reverse

from temba.request_logs.models import HTTPLog
from temba.templates.models import TemplateTranslation
from temba.tests import MockResponse, TembaTest

from ...models import Channel
from .type import WhatsAppCloudType


class WhatsAppCloudTypeTest(TembaTest):
    @override_settings(
        FACEBOOK_APPLICATION_ID="FB_APP_ID",
        FACEBOOK_APPLICATION_SECRET="FB_APP_SECRET",
        WHATSAPP_FACEBOOK_BUSINESS_ID="FB_BUSINESS_ID",
        WHATSAPP_ADMIN_SYSTEM_USER_TOKEN="WA_ADMIN_TOKEN",
        ALLOWED_WHATSAPP_FACEBOOK_BUSINESS_IDS=["2222222222222"],
    )
    @patch("temba.channels.types.whatsapp_cloud.views.randint")
    def test_claim(self, mock_randint):
        mock_randint.return_value = 111111

        Channel.objects.all().delete()
        self.login(self.admin)

        # remove any existing channels
        self.org.channels.update(is_active=False)

        connect_whatsapp_cloud_url = reverse("orgs.org_whatsapp_cloud_connect")
        claim_whatsapp_cloud_url = reverse("channels.types.whatsapp_cloud.claim")

        # make sure plivo is on the claim page
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertEqual(200, response.status_code)
        self.assertNotContains(response, claim_whatsapp_cloud_url)

        with patch("requests.get") as wa_cloud_get:
            wa_cloud_get.return_value = MockResponse(400, {})
            response = self.client.get(claim_whatsapp_cloud_url)

            self.assertEqual(response.status_code, 302)

            response = self.client.get(claim_whatsapp_cloud_url, follow=True)

            self.assertEqual(response.request["PATH_INFO"], "/users/login/")

        self.make_beta(self.admin)
        with patch("requests.get") as wa_cloud_get:
            wa_cloud_get.return_value = MockResponse(400, {})
            response = self.client.get(claim_whatsapp_cloud_url)

            self.assertEqual(response.status_code, 302)

            response = self.client.get(claim_whatsapp_cloud_url, follow=True)

            self.assertEqual(response.request["PATH_INFO"], connect_whatsapp_cloud_url)

        with patch("requests.get") as wa_cloud_get:
            wa_cloud_get.side_effect = [
                MockResponse(400, {}),
                # missing permissions
                MockResponse(
                    200,
                    json.dumps({"data": {"scopes": []}}),
                ),
                # success
                MockResponse(
                    200,
                    json.dumps(
                        {
                            "data": {
                                "scopes": [
                                    "business_management",
                                    "whatsapp_business_management",
                                    "whatsapp_business_messaging",
                                ]
                            }
                        }
                    ),
                ),
                MockResponse(
                    200,
                    json.dumps(
                        {
                            "data": {
                                "scopes": [
                                    "business_management",
                                    "whatsapp_business_management",
                                    "whatsapp_business_messaging",
                                ]
                            }
                        }
                    ),
                ),
                MockResponse(
                    200,
                    json.dumps(
                        {
                            "data": {
                                "scopes": [
                                    "business_management",
                                    "whatsapp_business_management",
                                    "whatsapp_business_messaging",
                                ]
                            }
                        }
                    ),
                ),
            ]
            response = self.client.get(connect_whatsapp_cloud_url)
            self.assertEqual(response.status_code, 200)

            # 400 status
            response = self.client.post(connect_whatsapp_cloud_url, dict(user_access_token="X" * 36), follow=True)
            self.assertEqual(
                response.context["form"].errors["__all__"][0], "Sorry account could not be connected. Please try again"
            )

            # missing permissions
            response = self.client.post(connect_whatsapp_cloud_url, dict(user_access_token="X" * 36), follow=True)
            self.assertEqual(
                response.context["form"].errors["__all__"][0], "Sorry account could not be connected. Please try again"
            )

            response = self.client.post(connect_whatsapp_cloud_url, dict(user_access_token="X" * 36))
            self.assertIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)
            self.assertEqual(response.url, claim_whatsapp_cloud_url)

            response = self.client.post(connect_whatsapp_cloud_url, dict(user_access_token="X" * 36), follow=True)
            self.assertEqual(response.status_code, 200)

            self.assertEqual(wa_cloud_get.call_args_list[0][0][0], "https://graph.facebook.com/v13.0/debug_token")
            self.assertEqual(
                wa_cloud_get.call_args_list[0][1],
                {"params": {"access_token": "FB_APP_ID|FB_APP_SECRET", "input_token": "X" * 36}},
            )

        # make sure the token is set on the session
        session = self.client.session
        session[Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN] = "user-token"
        session.save()

        self.assertIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

        with patch("requests.get") as wa_cloud_get:
            with patch("requests.post") as wa_cloud_post:

                wa_cloud_get.side_effect = [
                    # pre-process missing permissions
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "scopes": [
                                        "business_management",
                                        "whatsapp_business_messaging",
                                    ]
                                }
                            }
                        ),
                    ),
                ]

                response = self.client.get(claim_whatsapp_cloud_url, follow=True)

                self.assertFalse(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN in self.client.session)

        # make sure the token is set on the session
        session = self.client.session
        session[Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN] = "user-token"
        session.save()

        self.assertIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

        with patch("requests.get") as wa_cloud_get:
            with patch("requests.post") as wa_cloud_post:

                wa_cloud_get.side_effect = [
                    # pre-process for get
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "scopes": [
                                        "business_management",
                                        "whatsapp_business_management",
                                        "whatsapp_business_messaging",
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting target waba
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "granular_scopes": [
                                        {
                                            "scope": "business_management",
                                            "target_ids": [
                                                "2222222222222",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_management",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_messaging",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting waba details
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "id": "111111111111111",
                                "currency": "USD",
                                "message_template_namespace": "namespace-uuid",
                                "on_behalf_of_business_info": {"id": "2222222222222"},
                            }
                        ),
                    ),
                    # getting waba phone numbers
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": [
                                    {"id": "123123123", "display_phone_number": "1234", "verified_name": "WABA name"}
                                ]
                            }
                        ),
                    ),
                    # pre-process for post
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "scopes": [
                                        "business_management",
                                        "whatsapp_business_management",
                                        "whatsapp_business_messaging",
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting te credit line ID
                    MockResponse(200, json.dumps({"data": [{"id": "567567567"}]})),
                    # phone number verification status
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "verified_name": "WABA name",
                                "code_verification_status": "VERIFIED",
                                "display_phone_number": "1234",
                                "quality_rating": "GREEN",
                                "id": "123123123",
                            }
                        ),
                    ),
                ]

                wa_cloud_post.return_value = MockResponse(200, json.dumps({"success": "true"}))

                response = self.client.get(claim_whatsapp_cloud_url, follow=True)

                self.assertEqual(len(response.context["phone_numbers"]), 1)
                self.assertEqual(response.context["phone_numbers"][0]["waba_id"], "111111111111111")
                self.assertEqual(response.context["phone_numbers"][0]["phone_number_id"], "123123123")
                self.assertEqual(response.context["phone_numbers"][0]["business_id"], "2222222222222")
                self.assertEqual(response.context["phone_numbers"][0]["currency"], "USD")
                self.assertEqual(response.context["phone_numbers"][0]["verified_name"], "WABA name")

                post_data = response.context["form"].initial
                post_data["number"] = "1234"
                post_data["verified_name"] = "WABA name"
                post_data["phone_number_id"] = "123123123"
                post_data["waba_id"] = "111111111111111"
                post_data["business_id"] = "2222222222222"
                post_data["currency"] = "USD"
                post_data["message_template_namespace"] = "namespace-uuid"

                response = self.client.post(claim_whatsapp_cloud_url, post_data, follow=True)
                self.assertEqual(200, response.status_code)

                self.assertNotIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

                self.assertEqual(4, wa_cloud_post.call_count)

                self.assertEqual(
                    "https://graph.facebook.com/v13.0/111111111111111/assigned_users",
                    wa_cloud_post.call_args_list[0][0][0],
                )
                self.assertEqual(
                    {"Authorization": "Bearer WA_ADMIN_TOKEN"}, wa_cloud_post.call_args_list[0][1]["headers"]
                )

                self.assertEqual(
                    "https://graph.facebook.com/v13.0/567567567/whatsapp_credit_sharing_and_attach",
                    wa_cloud_post.call_args_list[1][0][0],
                )
                self.assertEqual(
                    "https://graph.facebook.com/v13.0/111111111111111/subscribed_apps",
                    wa_cloud_post.call_args_list[2][0][0],
                )

                self.assertEqual(
                    "https://graph.facebook.com/v13.0/123123123/register", wa_cloud_post.call_args_list[3][0][0]
                )
                self.assertEqual(
                    {"messaging_product": "whatsapp", "pin": "111111"}, wa_cloud_post.call_args_list[3][1]["data"]
                )

                channel = Channel.objects.get()

                self.assertEqual(
                    response.request["PATH_INFO"],
                    reverse("channels.channel_read", args=(channel.uuid,)),
                )

                self.assertEqual("1234 - WABA name", channel.name)
                self.assertEqual("123123123", channel.address)
                self.assertEqual("WAC", channel.channel_type)
                self.assertTrue(channel.type.has_attachment_support(channel))

                self.assertEqual("1234", channel.config["wa_number"])
                self.assertEqual("WABA name", channel.config["wa_verified_name"])
                self.assertEqual("111111111111111", channel.config["wa_waba_id"])
                self.assertEqual("USD", channel.config["wa_currency"])
                self.assertEqual("2222222222222", channel.config["wa_business_id"])
                self.assertEqual("111111", channel.config["wa_pin"])
                self.assertEqual("namespace-uuid", channel.config["wa_message_template_namespace"])

                response = self.client.get(reverse("channels.types.whatsapp_cloud.request_code", args=(channel.uuid,)))
                self.assertEqual(200, response.status_code)

                # request verification code
                response = self.client.post(
                    reverse("channels.types.whatsapp_cloud.request_code", args=(channel.uuid,)), dict(), follow=True
                )
                self.assertEqual(200, response.status_code)

                self.assertEqual(
                    "https://graph.facebook.com/v13.0/123123123/request_code", wa_cloud_post.call_args[0][0]
                )

                # submit verification code
                response = self.client.post(
                    reverse("channels.types.whatsapp_cloud.verify_code", args=(channel.uuid,)),
                    dict(code="000000"),
                    follow=True,
                )
                self.assertEqual(200, response.status_code)

                self.assertEqual("https://graph.facebook.com/v13.0/123123123/register", wa_cloud_post.call_args[0][0])
                self.assertEqual(
                    {"messaging_product": "whatsapp", "pin": "111111"}, wa_cloud_post.call_args[1]["data"]
                )

        # make sure the token is set on the session
        session = self.client.session
        session[Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN] = "user-token"
        session.save()

        self.assertIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

        with patch("requests.get") as wa_cloud_get:
            with patch("requests.post") as wa_cloud_post:

                wa_cloud_get.side_effect = [
                    # pre-process for get
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "scopes": [
                                        "business_management",
                                        "whatsapp_business_management",
                                        "whatsapp_business_messaging",
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting target waba
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "granular_scopes": [
                                        {
                                            "scope": "business_management",
                                            "target_ids": [
                                                "2222222222222",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_management",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_messaging",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting waba details
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "id": "111111111111111",
                                "currency": "USD",
                                "message_template_namespace": "namespace-uuid",
                                "on_behalf_of_business_info": {"id": "2222222222222"},
                            }
                        ),
                    ),
                    # getting waba phone numbers
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": [
                                    {"id": "123123123", "display_phone_number": "1234", "verified_name": "WABA name"}
                                ]
                            }
                        ),
                    ),
                    # pre-process for post
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "scopes": [
                                        "business_management",
                                        "whatsapp_business_management",
                                        "whatsapp_business_messaging",
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting target waba
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": {
                                    "granular_scopes": [
                                        {
                                            "scope": "business_management",
                                            "target_ids": [
                                                "2222222222222",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_management",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                        {
                                            "scope": "whatsapp_business_messaging",
                                            "target_ids": [
                                                "111111111111111",
                                            ],
                                        },
                                    ]
                                }
                            }
                        ),
                    ),
                    # getting waba details
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "id": "111111111111111",
                                "currency": "USD",
                                "message_template_namespace": "namespace-uuid",
                                "on_behalf_of_business_info": {"id": "2222222222222"},
                            }
                        ),
                    ),
                    # getting waba phone numbers
                    MockResponse(
                        200,
                        json.dumps(
                            {
                                "data": [
                                    {"id": "123123123", "display_phone_number": "1234", "verified_name": "WABA name"}
                                ]
                            }
                        ),
                    ),
                    # getting te credit line ID
                    MockResponse(200, json.dumps({"data": [{"id": "567567567"}]})),
                ]

                wa_cloud_post.return_value = MockResponse(200, json.dumps({"success": "true"}))

                response = self.client.get(claim_whatsapp_cloud_url, follow=True)

                wa_cloud_get.reset_mock()

                response = self.client.post(claim_whatsapp_cloud_url, post_data, follow=True)
                self.assertEqual(200, response.status_code)
                self.assertEqual(
                    response.context["form"].errors["__all__"][0],
                    "That number is already connected (1234)",
                )

    def test_clear_session_token(self):
        Channel.objects.all().delete()
        self.login(self.admin)

        clear_session_token_url = reverse("channels.types.whatsapp_cloud.clear_session_token")
        response = self.client.get(clear_session_token_url)
        self.assertEqual(200, response.status_code)

        self.assertNotIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

        session = self.client.session
        session[Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN] = "user-token"
        session.save()

        self.assertIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

        response = self.client.get(clear_session_token_url)
        self.assertEqual(200, response.status_code)

        self.assertNotIn(Channel.CONFIG_WHATSAPP_CLOUD_USER_TOKEN, self.client.session)

    @override_settings(WHATSAPP_ADMIN_SYSTEM_USER_TOKEN="WA_ADMIN_TOKEN")
    @patch("requests.get")
    def test_get_api_templates(self, mock_get):
        TemplateTranslation.objects.all().delete()
        Channel.objects.all().delete()

        channel = self.create_channel(
            "WAC",
            "WABA name",
            "123123123",
            config={
                "wa_waba_id": "111111111111111",
            },
        )

        mock_get.side_effect = [
            RequestException("Network is unreachable", response=MockResponse(100, "")),
            MockResponse(400, '{ "meta": { "success": false } }'),
            MockResponse(200, '{"data": ["foo", "bar"]}'),
            MockResponse(
                200,
                '{"data": ["foo"], "paging": {"cursors": {"after": "MjQZD"}, "next": "https://graph.facebook.com/v14.0/111111111111111/message_templates?after=MjQZD" } }',
            ),
            MockResponse(200, '{"data": ["bar"], "paging": {"cursors": {"after": "MjQZD"} } }'),
        ]

        # RequestException check HTTPLog
        templates_data, no_error = WhatsAppCloudType().get_api_templates(channel)
        self.assertEqual(1, HTTPLog.objects.filter(log_type=HTTPLog.WHATSAPP_TEMPLATES_SYNCED).count())
        self.assertFalse(no_error)
        self.assertEqual([], templates_data)

        # should be empty list with an error flag if fail with API
        templates_data, no_error = WhatsAppCloudType().get_api_templates(channel)
        self.assertFalse(no_error)
        self.assertEqual([], templates_data)

        # success no error and list
        templates_data, no_error = WhatsAppCloudType().get_api_templates(channel)
        self.assertTrue(no_error)
        self.assertEqual(["foo", "bar"], templates_data)

        mock_get.assert_called_with(
            "https://graph.facebook.com/v14.0/111111111111111/message_templates",
            params={"limit": 255},
            headers={"Authorization": "Bearer WA_ADMIN_TOKEN"},
        )

        # success no error and pagination
        templates_data, no_error = WhatsAppCloudType().get_api_templates(channel)
        self.assertTrue(no_error)
        self.assertEqual(["foo", "bar"], templates_data)

        mock_get.assert_has_calls(
            [
                call(
                    "https://graph.facebook.com/v14.0/111111111111111/message_templates",
                    params={"limit": 255},
                    headers={"Authorization": "Bearer WA_ADMIN_TOKEN"},
                ),
                call(
                    "https://graph.facebook.com/v14.0/111111111111111/message_templates?after=MjQZD",
                    params={"limit": 255},
                    headers={"Authorization": "Bearer WA_ADMIN_TOKEN"},
                ),
            ]
        )
