from twilio.base.exceptions import TwilioRestException

from django.utils.translation import ugettext_lazy as _

from temba.channels.types.bandwidth.views import ClaimView
from temba.contacts.models import TEL_SCHEME

from ...models import ChannelType


class BandwidthType(ChannelType):
    """
    An IST Bandwidth channel
    """

    code = "BWD"
    category = ChannelType.Category.PHONE

    courier_url = r"^bwd/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive|status)$"

    name = "Bandwidth"
    icon = "icon-channel-bandwidth"
    claim_blurb = _(
        """Easily add a two way number you have configured with <a href="https://www.bandwidth.com/">Bandwidth</a> using their APIs."""
    )
    claim_view = ClaimView

    schemes = [TEL_SCHEME]
    max_length = 1600

    def deactivate(self, channel):
        config = channel.config
        client = channel.org.get_bandwidth_messaging_client()
        number_update_args = dict()

        if not channel.is_delegate_sender():
            number_update_args["sms_application_sid"] = ""

        if channel.supports_ivr():
            number_update_args["voice_application_sid"] = ""

        try:
            try:
                number_sid = channel.bod or channel.config.get("number_sid")
                client.api.incoming_phone_numbers.get(number_sid).update(**number_update_args)
            except Exception:
                if client:
                    matching = client.api.incoming_phone_numbers.stream(phone_number=channel.address)
                    first_match = next(matching, None)
                    if first_match:
                        client.api.incoming_phone_numbers.get(first_match.sid).update(**number_update_args)

            if "application_sid" in config:
                try:
                    client.api.applications.get(sid=config["application_sid"]).delete()
                except TwilioRestException:  # pragma: no cover
                    pass

        except TwilioRestException as e:
            # we swallow 20003 which means our bandwidth key is no longer valid
            if e.code != 20003:
                raise e
