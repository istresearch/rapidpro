"""
Alternative to overwriting a file with customizations/any is to provide 'surgical overrides' in
the form of methods put into specific classes "after initialization, but before handle-ization".

Import this file just after all the urls in the main urls.py and run its overrides.
"""
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

def _TrackUser(self):  # pragma: no cover
    """
    Should the current user be tracked
    """
    # track if "is logged in" and not DEV instance
    if self.is_authenticated and not self.is_anonymous and settings.IS_PROD:
        return True
    else:
        return False

def RunEngageOverrides():
    """
    Overrides that need to be conducted at the tail end of temba/urls.py
    """
    from django.contrib.auth.models import AnonymousUser, User
    User.track_user = _TrackUser
    User.using_token = False  # default optional property to False so it exists.
    AnonymousUser.track_user = _TrackUser

    from engage.channels.types.postmaster.schemes import PM_Schemes, PM_Scheme_Labels, PM_Scheme_Icons
    #from engage.utils.strings import cap_words
    from temba.contacts.models import URN as TembaURN
    Processed_TembaURN_Scheme_Choices = (
        # The lazy string translation means we cannot just cap the words in use, but instead use the Django
        # Translation stuff: https://docs.djangoproject.com/en/4.0/topics/i18n/translation/
        # TODO instead of overriding their string IDs, we should update the translation for en_US, but
        #   that requires a follow-up text-bin utility which build process lacks currently.
        #(key, cap_words(val)) for key, val in TembaURN.SCHEME_CHOICES
        (TembaURN.TEL_SCHEME, _("Phone Number")),
        (TembaURN.FACEBOOK_SCHEME, _("Facebook Identifier")),
        (TembaURN.TWITTER_SCHEME, _("Twitter Handle")),
        (TembaURN.TWITTERID_SCHEME, _("Twitter ID")),
        (TembaURN.VIBER_SCHEME, _("Viber Identifier")),
        (TembaURN.LINE_SCHEME, _("LINE Identifier")),
        (TembaURN.TELEGRAM_SCHEME, _("Telegram Identifier")),
        (TembaURN.EMAIL_SCHEME, _("Email Address")),
        (TembaURN.EXTERNAL_SCHEME, _("External Identifier")),
        (TembaURN.JIOCHAT_SCHEME, _("JioChat Identifier")),
        (TembaURN.WECHAT_SCHEME, _("WeChat Identifier")),
        (TembaURN.FCM_SCHEME, _("Firebase Cloud Messaging Identifier")),
        (TembaURN.WHATSAPP_SCHEME, _("WhatsApp Identifier")),
        (TembaURN.FRESHCHAT_SCHEME, _("Freshchat Identifier")),
        (TembaURN.VK_SCHEME, _("VK Identifier")),
        (TembaURN.ROCKETCHAT_SCHEME, _("RocketChat Identifier")),
        (TembaURN.DISCORD_SCHEME, _("Discord Identifier")),
    ) + tuple([ t[1] for t in sorted((lambda x: [[y[1].split(" ")[1], y] for y in x])(PM_Scheme_Labels)) ]) # Sort PM alphabetically

    # URN is a static-only class, add in our needs
    from temba.contacts.models import URN as TembaURN
    for key, value in PM_Schemes.__dict__.items():
        if not (key.startswith('__') and key.endswith('__')):
            setattr(TembaURN, key, value)
    TembaURN.SCHEME_CHOICES = Processed_TembaURN_Scheme_Choices
    TembaURN.VALID_SCHEMES = {s[0] for s in TembaURN.SCHEME_CHOICES}
    #debug
    #for key, value in TembaURN.__dict__.items():
    #    if not (key.startswith('__') and key.endswith('__')):
    #        print(f"URN.{key}={value}")

    # icons for schemes are kept in a separate class for some reason
    from temba.contacts.templatetags.contacts import URN_SCHEME_ICONS
    URN_SCHEME_ICONS.update(PM_Scheme_Icons)

    from django.contrib.auth.models import User
    from engage.orgs.models import get_user_orgs
    User.get_user_orgs = get_user_orgs

    # cannot use OrgHomeMixin due to circular unit reference; override def here.
    from temba.orgs.views import OrgCRUDL as TembaOrgViews
    from engage.orgs.home import OrgHomeMixin as EngageOrgViews
    TembaOrgViews.Home.orig_get_gear_links = TembaOrgViews.Home.get_gear_links
    TembaOrgViews.Home.get_gear_links = EngageOrgViews.Home.get_gear_links
    TembaOrgViews.Home.derive_formax_sections = EngageOrgViews.Home.derive_formax_sections

    # override the date picker widget with one we like better
    import smartmin.widgets
    from engage.msgs.datepicker import DatePickerMedia
    smartmin.widgets.DatePickerWidget.Media = DatePickerMedia

    from engage.msgs.msgcontent import ListMsgContentMixin
    from temba.msgs.views import InboxView as BaseMsgInboxView
    BaseMsgInboxView.__bases__ = (ListMsgContentMixin,) + BaseMsgInboxView.__bases__

    from temba.msgs.views import MsgCRUDL
    from engage.msgs.inbox_msgfailed import ViewInboxFailedMsgsMixin
    # introduce anything "new" we wish to add from the Mixin by adding it first in __bases__ list.
    MsgCRUDL.Failed.__bases__ = (ViewInboxFailedMsgsMixin,) + MsgCRUDL.Failed.__bases__
    # override existing methods we need as local defs hide our mixin defs.
    setattr(MsgCRUDL.Failed, 'get_bulk_actions', ViewInboxFailedMsgsMixin.get_bulk_actions)

    from engage.msgs.exporter import MsgExporter
    setattr(MsgCRUDL.Export, 'form_valid', MsgExporter.form_valid)

    from temba.mailroom.events import event_renderers
    from engage.mailroom.events import getHistoryContentFromMsg, getHistoryContentFromChannelEvent
    from temba.msgs.models import Msg, ChannelEvent
    event_renderers[Msg] = getHistoryContentFromMsg
    event_renderers[ChannelEvent] = getHistoryContentFromChannelEvent

    from temba.contacts.templatetags.contacts import register
    from engage.contacts.templatetags import scheme_icon
    register.filter(scheme_icon)

    from temba.api import models
    from engage.api.permissions import SSLPermission as EngageSSLPermission
    models.SSLPermission = EngageSSLPermission
