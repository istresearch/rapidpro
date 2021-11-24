from unittest.mock import patch

from bandwidth.messaging.api_exception_module import BandwidthMessageAPIException

from django.urls import reverse

from temba.channels.models import Channel
from temba.orgs.models import BW_ACCOUNT_SID, BW_ACCOUNT_TOKEN
from temba.tests import TembaTest
from temba.tests.bandwidth import MockRequestValidator


class BandwidthTypeTest(TembaTest):
    @patch("bandwidth.request_validator.RequestValidator", MockRequestValidator)
    def test_claim(self):
        self.login(self.admin)

        claim_bandwidth = reverse("channels.types.bandwidth.claim")

        # remove any existing channels
        self.org.channels.update(is_active=False)

        # make sure bandwidth is on the claim page
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertContains(response, "Bandwidth")

        response = self.client.get(claim_bandwidth)
        self.assertEqual(response.status_code, 302)
        response = self.client.get(claim_bandwidth, follow=True)
        self.assertEqual(response.request["PATH_INFO"], reverse("orgs.org_bandwidth_connect"))

        # attach a Bandwidth accont to the org
        self.org.config = {BW_ACCOUNT_SID: "bw-account-sid", BW_ACCOUNT_TOKEN: "bw-account-token"}
        self.org.save()

        # hit the claim page, should now have a claim bandwidth link
        response = self.client.get(reverse("channels.channel_claim"))
        self.assertContains(response, claim_bandwidth)

        response = self.client.get(claim_bandwidth)
        self.assertEqual(200, response.status_code)

        with patch("temba.orgs.models.Org.get_bandwidth_messaging_client") as mock_get_bandwidth_client:
            mock_get_bandwidth_client.return_value = None

            response = self.client.get(claim_bandwidth)
            self.assertRedirects(response, reverse("orgs.org_bandwidth_connect"))

            mock_get_bandwidth_client.side_effect = BandwidthMessageAPIException(
                401, "http://bandwidth", msg="Authentication Failure", code=20003
            )

            response = self.client.get(claim_bandwidth)
            self.assertRedirects(response, reverse("orgs.org_bandwidth_connect"))

        bandwidth_channel = self.org.channels.all().first()
        # make channel support sms by clearing both applications
        bandwidth_channel.role = Channel.ROLE_SEND + Channel.ROLE_RECEIVE + Channel.ROLE_ANSWER
        bandwidth_channel.save()
        self.assertEqual("BWD", bandwidth_channel.channel_type)

