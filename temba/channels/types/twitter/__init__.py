from __future__ import unicode_literals, absolute_import

import six
import time
import json

from django.utils.translation import ugettext_lazy as _
from temba.contacts.models import Contact, TWITTER_SCHEME
from temba.msgs.models import WIRED
from temba.utils.twitter import TembaTwython
from .views import ClaimView
from ...models import Channel, ChannelType, SendException
from ...tasks import MageStreamAction, notify_mage_task


class TwitterType(ChannelType):
    """
    A Twitter channel which uses Mage to stream DMs for a handle which has given access to a Twitter app configured for
    this deployment.
    """
    code = 'TT'
    category = ChannelType.Category.SOCIAL_MEDIA

    name = "Twitter"
    icon = 'icon-twitter'

    claim_blurb = _("""Add a <a href="http://twitter.com">Twitter</a> account to send messages as direct messages.""")
    claim_view = ClaimView

    scheme = TWITTER_SCHEME
    max_length = 10000
    show_config_page = False
    free_sending = True

    FATAL_403S = ("messages to this user right now",  # handle is suspended
                  "users who are not following you")  # handle no longer follows us

    def activate(self, channel):
        # tell Mage to activate this channel
        notify_mage_task.delay(channel.uuid, MageStreamAction.activate.name)

    def deactivate(self, channel):
        # tell Mage to deactivate this channel
        notify_mage_task.delay(channel.uuid, MageStreamAction.deactivate.name)

    def get_context_metadata(self, msg, text):
        data = { 
            "event": {
                "type": "message_create",
                "message_create":{
                    "target":{
                        "recipient_id": msg.urn_path
                    },
                    "message_data": {
                        "text": text,
                        "quick_reply":{    
                                "type": "options",
                                "options": []
                        }
                    }
                }
            } 
        }
        metadata =  json.loads(msg.metadata)
        if metadata.get('quick_reply'):
            quick_replies = metadata.get('quick_reply')
            for quick_reply in quick_replies:
                data["event"]["message_create"]["message_data"]["quick_reply"]["options"].append(
                    { "label": quick_reply["title"], "metadata": quick_reply["payload"] })
        else:
            pass
            
        return data
    
    def send(self, channel, msg, text):
        start = time.time()

        try:
            if hasattr(msg, 'metadata'):
                headers = { 'headers': {str('Content-Type'): str('application/json') } }
                twitter = TembaTwython.from_channel(channel, headers=headers)
                dm = twitter.send_direct_message_with_events(self.get_context_metadata(msg, text))
            else:
                twitter = TembaTwython.from_channel(channel)
                dm = twitter.send_direct_message(screen_name=msg.urn_path, text=text)
        except Exception as e:
            error_code = getattr(e, 'error_code', 400)
            fatal = False

            if error_code == 404:  # handle doesn't exist
                fatal = True
            elif error_code == 403:
                for err in self.FATAL_403S:
                    if six.text_type(e).find(err) >= 0:
                        fatal = True
                        break

            # if message can never be sent, stop them contact
            if fatal:
                contact = Contact.objects.get(id=msg.contact)
                contact.stop(contact.modified_by)

            raise SendException(str(e), events=twitter.events, fatal=fatal, start=start)

        external_id = dm['id']
        Channel.success(channel, msg, WIRED, start, events=twitter.events, external_id=external_id)
