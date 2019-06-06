from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import Group
from django.test import override_settings
from django.utils import timezone

from temba.api.models import APIToken, WebHookEvent, WebHookResult
from temba.api.tasks import trim_webhook_event_task
from temba.msgs.models import FAILED
from temba.orgs.models import ALL_EVENTS
from temba.tests import MockResponse, TembaTest


class APITokenTest(TembaTest):
    def setUp(self):
        super().setUp()

        self.create_secondary_org()

        self.admins_group = Group.objects.get(name="Administrators")
        self.editors_group = Group.objects.get(name="Editors")
        self.surveyors_group = Group.objects.get(name="Surveyors")

        self.org2.surveyors.add(self.admin)  # our admin can act as surveyor for other org

    def test_get_or_create(self):
        token1 = APIToken.get_or_create(self.org, self.admin)
        self.assertEqual(token1.org, self.org)
        self.assertEqual(token1.user, self.admin)
        self.assertEqual(token1.role, self.admins_group)
        self.assertTrue(token1.key)
        self.assertEqual(str(token1), token1.key)

        # tokens for different roles with same user should differ
        token2 = APIToken.get_or_create(self.org, self.admin, self.admins_group)
        token3 = APIToken.get_or_create(self.org, self.admin, self.editors_group)
        token4 = APIToken.get_or_create(self.org, self.admin, self.surveyors_group)

        self.assertEqual(token1, token2)
        self.assertNotEqual(token1, token3)
        self.assertNotEqual(token1, token4)
        self.assertNotEqual(token1.key, token3.key)

        # tokens with same role for different users should differ
        token5 = APIToken.get_or_create(self.org, self.editor)

        self.assertNotEqual(token3, token5)

        APIToken.get_or_create(self.org, self.surveyor)

        # can't create token for viewer users or other users using viewers role
        self.assertRaises(ValueError, APIToken.get_or_create, self.org, self.admin, Group.objects.get(name="Viewers"))
        self.assertRaises(ValueError, APIToken.get_or_create, self.org, self.user)

    def test_get_orgs_for_role(self):
        self.assertEqual(set(APIToken.get_orgs_for_role(self.admin, self.admins_group)), {self.org})
        self.assertEqual(set(APIToken.get_orgs_for_role(self.admin, self.surveyors_group)), {self.org, self.org2})

    def test_get_allowed_roles(self):
        self.assertEqual(
            set(APIToken.get_allowed_roles(self.org, self.admin)),
            {self.admins_group, self.editors_group, self.surveyors_group},
        )
        self.assertEqual(
            set(APIToken.get_allowed_roles(self.org, self.editor)), {self.editors_group, self.surveyors_group}
        )
        self.assertEqual(set(APIToken.get_allowed_roles(self.org, self.surveyor)), {self.surveyors_group})
        self.assertEqual(set(APIToken.get_allowed_roles(self.org, self.user)), set())

        # user from another org has no API roles
        self.assertEqual(set(APIToken.get_allowed_roles(self.org, self.admin2)), set())

    def test_get_default_role(self):
        self.assertEqual(APIToken.get_default_role(self.org, self.admin), self.admins_group)
        self.assertEqual(APIToken.get_default_role(self.org, self.editor), self.editors_group)
        self.assertEqual(APIToken.get_default_role(self.org, self.surveyor), self.surveyors_group)
        self.assertIsNone(APIToken.get_default_role(self.org, self.user))

        # user from another org has no API roles
        self.assertIsNone(APIToken.get_default_role(self.org, self.admin2))


class WebHookTest(TembaTest):
    def setUp(self):
        super().setUp()
        self.joe = self.create_contact("Joe Blow", "0788123123")
        settings.SEND_WEBHOOKS = True

    def tearDown(self):
        super().tearDown()
        settings.SEND_WEBHOOKS = False

    def setupChannel(self):
        org = self.channel.org
        org.webhook = {"url": "http://fake.com/webhook.php"}
        org.webhook_events = ALL_EVENTS
        org.save()

        self.channel.address = "+250788123123"
        self.channel.save()

    def test_webhook_event_trim_task(self):
        sms = self.create_msg(contact=self.joe, direction="I", status="H", text="I'm gonna pop some tags")
        self.setupChannel()
        now = timezone.now()

        with patch("requests.Session.send") as mock:
            mock.return_value = MockResponse(200, "Hello World")

            # trigger an event
            WebHookEvent.trigger_sms_event(WebHookEvent.TYPE_SMS_RECEIVED, sms, now)
            event = WebHookEvent.objects.get()

            five_hours_ago = timezone.now() - timedelta(hours=5)
            event.created_on = five_hours_ago
            event.save()
            WebHookResult.objects.all().update(created_on=five_hours_ago)

            with override_settings(SUCCESS_LOGS_TRIM_TIME=0):
                trim_webhook_event_task()
                self.assertTrue(WebHookEvent.objects.all())
                self.assertTrue(WebHookResult.objects.all())

            with override_settings(SUCCESS_LOGS_TRIM_TIME=12):
                trim_webhook_event_task()
                self.assertTrue(WebHookEvent.objects.all())
                self.assertTrue(WebHookResult.objects.all())

            with override_settings(SUCCESS_LOGS_TRIM_TIME=2):
                trim_webhook_event_task()
                self.assertFalse(WebHookEvent.objects.all())
                self.assertFalse(WebHookResult.objects.all())

            WebHookEvent.trigger_sms_event(WebHookEvent.TYPE_SMS_RECEIVED, sms, now)
            event = WebHookEvent.objects.get()

            five_hours_ago = timezone.now() - timedelta(hours=5)
            event.created_on = five_hours_ago
            event.status = FAILED
            event.save()
            WebHookResult.objects.all().update(status_code=401, created_on=five_hours_ago)

            with override_settings(ALL_LOGS_TRIM_TIME=0):
                trim_webhook_event_task()
                self.assertTrue(WebHookEvent.objects.all())
                self.assertTrue(WebHookResult.objects.all())

            with override_settings(ALL_LOGS_TRIM_TIME=12):
                trim_webhook_event_task()
                self.assertTrue(WebHookEvent.objects.all())
                self.assertTrue(WebHookResult.objects.all())

            with override_settings(ALL_LOGS_TRIM_TIME=2):
                trim_webhook_event_task()
                self.assertFalse(WebHookEvent.objects.all())
                self.assertFalse(WebHookResult.objects.all())
