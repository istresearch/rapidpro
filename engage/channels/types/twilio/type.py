import logging

from django.urls import reverse

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.models import Channel
from temba.channels.types.twilio.type import TwilioType


logger = logging.getLogger()

class TwilioTypeOverrides(ClassOverrideMixinMustBeFirst, TwilioType):

    def enable_flow_server(self, channel):
        """
        Called when our organization is switched to being flow server enabled,
        for Twilio we have to switch our IVR
        status and incoming calls to point to mailroom URLs.
        """
        # noop if we don't support ivr or are a shortcode
        if not channel.supports_ivr() or len(channel.address) <= 6:
            return

        org = channel.org
        client = org.get_twilio_client()
        config = channel.config

        base_url = "https://" + config.get(Channel.CONFIG_CALLBACK_DOMAIN, org.get_brand_domain())

        # build our URLs
        channel_uuid = str(channel.uuid)
        mr_status_url = base_url + reverse("mailroom.ivr_handler", args=[channel_uuid, "status"])
        mr_incoming_url = base_url + reverse("mailroom.ivr_handler", args=[channel_uuid, "incoming"])

        # update the voice URLs on our app
        app = client.api.applications.get(sid=config["application_sid"])
        app.update(
            voice_method="POST",
            voice_url=mr_incoming_url,
            status_callback_method="POST",
            status_callback=mr_status_url,
        )
    #enddef enable_flow_server

#endclass TwilioTypeOverrides
