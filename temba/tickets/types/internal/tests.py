from django.urls import reverse

from temba.tests import TembaTest
from temba.tickets.models import Ticketer

from .type import InternalType


class InternalTypeTest(TembaTest):
    def test_is_available_to(self):
        self.assertTrue(InternalType().is_available_to(self.admin))

        Ticketer.create(org=self.org, user=self.admin, ticketer_type=InternalType.slug, config={}, name=f"Internal")

        # not if they already created one
        self.assertFalse(InternalType().is_available_to(self.admin))

    def test_connect(self):
        connect_url = reverse("tickets.types.internal.connect")

        response = self.client.get(connect_url)
        self.assertLoginRedirect(response)

        self.login(self.admin)

        response = self.client.get(connect_url)

        self.assertEqual(["loc"], list(response.context["form"].fields.keys()))

        self.client.post(connect_url, {})

        ticketer = Ticketer.objects.get(ticketer_type="internal")

        self.assertEqual("RapidPro Tickets", ticketer.name)
