from __future__ import unicode_literals, absolute_import

import time
from time import sleep

import regex

from django.utils.translation import ugettext_lazy as _

from temba.channels.models import ChannelType, Channel, SendException
from temba.channels.views import UpdateNexmoForm
from temba.channels.types.nexmo.views import ClaimView
from temba.contacts.models import TEL_SCHEME
from temba.msgs.models import SENT
from temba.orgs.models import NEXMO_APP_ID, NEXMO_APP_PRIVATE_KEY, NEXMO_SECRET, NEXMO_KEY
from temba.utils.nexmo import NexmoClient


class NexmoType(ChannelType):
    """
    An Nexmo channel
    """

    code = 'NX'
    category = ChannelType.Category.PHONE

    name = "Nexmo"
    icon = "icon-channel-nexmo"

    claim_blurb = _("""Easily add a two way number you have configured with <a href="https://www.twilio.com/">Twilio</a> using their APIs.""")
    claim_view = ClaimView

    update_form = UpdateNexmoForm

    schemes = [TEL_SCHEME]
    max_length = 1600
    max_tps = 1

    ivr_protocol = ChannelType.IVRProtocol.IVR_PROTOCOL_NCCO

    def is_available_to(self, user):
        org = user.get_org()
        return org.is_connected_to_nexmo()

    def send(self, channel, msg, text):

        client = NexmoClient(channel.org_config[NEXMO_KEY], channel.org_config[NEXMO_SECRET],
                             channel.org_config[NEXMO_APP_ID], channel.org_config[NEXMO_APP_PRIVATE_KEY])
        start = time.time()

        event = None
        attempts = 0
        while not event:
            try:
                (message_id, event) = client.send_message_via_nexmo(channel.address, msg.urn_path, text)
            except SendException as e:
                match = regex.match(r'.*Throughput Rate Exceeded - please wait \[ (\d+) \] and retry.*', e.events[0].response_body)

                # this is a throughput failure, attempt to wait up to three times
                if match and attempts < 3:
                    sleep(float(match.group(1)) / 1000)
                    attempts += 1
                else:
                    raise e

        Channel.success(channel, msg, SENT, start, event=event, external_id=message_id)
