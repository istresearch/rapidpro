# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function, unicode_literals

import telegram
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from temba.contacts.models import TELEGRAM_SCHEME
from .views import ClaimView
from ...models import ChannelType


class TelegramType(ChannelType):
    """
    A Telegram bot channel
    """
    code = 'TG'
    category = ChannelType.Category.SOCIAL_MEDIA

    name = "Telegram"
    icon = 'icon-telegram'
    show_config_page = False

    claim_blurb = _("""Add a <a href="https://telegram.org">Telegram</a> bot to send and receive messages to Telegram
    users for free. Your users will need an Android, Windows or iOS device and a Telegram account to send and receive
    messages.""")
    claim_view = ClaimView

    schemes = [TELEGRAM_SCHEME]
    max_length = 1600
    attachment_support = True
    free_sending = True

    def activate(self, channel):
        config = channel.config
        bot = telegram.Bot(config['auth_token'])
        bot.set_webhook("https://" + channel.callback_domain + reverse('courier.tg', args=[channel.uuid]))

    def deactivate(self, channel):
        config = channel.config
        bot = telegram.Bot(config['auth_token'])
        bot.delete_webhook()
