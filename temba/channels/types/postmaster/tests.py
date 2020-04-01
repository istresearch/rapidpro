from unittest.mock import patch

from django.urls import reverse

from temba.channels.models import Channel
from temba.tests import TembaTest
from twilio.request_validator import RequestValidator


class PostmasterTypeTest(TembaTest):
    @patch("postmaster.request_validator.RequestValidator", MockRequestValidator)
    def test_claim(self):
        self.login(self.admin)

        claim_postmaster = reverse("channels.types.postmaster.claim")

        # remove any existing channels
        self.org.channels.update(is_active=False)

        import temba.channels.models.Channel as PMChannel

        # make sure postmaster is on the claim page
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertContains(response, "Postmaster")

        response = self.client.get(claim_postmaster)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(claim_postmaster, follow=True)
        self.assertEqual(response.request["PATH_INFO"], reverse("orgs.org_postmaster_connect"))

        # attach a Postmaster device to the org
        self.org.config = {PMChannel.CONFIG_DEVICE_ID: "pm-device-id", PMChannel.CONFIG_CHAT_MODE: "pm-chat-mode"}
        self.org.save()

        # hit the claim page, should now have a claim postmaster link
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertContains(response, claim_postmaster)

        response = self.client.get(claim_postmaster)
        self.assertEqual(200, response.status_code)

        with patch("temba.orgs.models.Org.get_postmaster_messaging_client") as mock_get_postmaster_client:
            mock_get_postmaster_client.return_value = None

            response = self.client.get(claim_postmaster)
            self.assertRedirects(response, reverse("orgs.org_postmaster_connect"))

            mock_get_postmaster_client.side_effect = Exception(
                401, "http://postmaster", msg="Authentication Failure", code=20003
            )

            response = self.client.get(claim_postmaster)
            self.assertRedirects(response, reverse("orgs.org_postmaster_connect"))

        postmaster_channel = self.org.channels.all().first()
        # make channel support sms by clearing both applications
        postmaster_channel.role = Channel.ROLE_SEND + Channel.ROLE_RECEIVE + Channel.ROLE_ANSWER
        postmaster_channel.save()
        self.assertEqual("PSMS", postmaster_channel.channel_type)


class MockRequestValidator(RequestValidator):
    def __init__(self, token):
        pass

    def validate(self, url, post, signature):
        return True