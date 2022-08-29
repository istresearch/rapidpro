"""
Alternative to overwriting a file with customizations/any is to provide 'surgical overrides' in
the form of methods put into specific classes "after initialization, but before handle-ization".

Import this file just after all the urls in the main urls.py and run its overrides.
"""
from django.utils.translation import gettext_lazy as _


class EngageOverrides:
    ENGAGE_OVERRIDES_RAN: bool = False

    @classmethod
    def RunEngageOverrides(cls):
        """
        Overrides that need to be conducted at the tail end of temba/urls.py
        """
        #logging.debug('Ran? ' + str(cls.ENGAGE_OVERRIDES_RAN))
        if cls.ENGAGE_OVERRIDES_RAN:
            return

        from engage.auth.account import UserOverrides, AnonUserOverrides
        UserOverrides.setClassOverrides()
        AnonUserOverrides.setClassOverrides()

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
            #endif
        #endfor each scheme
        TembaURN.SCHEME_CHOICES = Processed_TembaURN_Scheme_Choices
        TembaURN.VALID_SCHEMES = {s[0] for s in TembaURN.SCHEME_CHOICES}
        #debug
        #for key, value in TembaURN.__dict__.items():
        #    if not (key.startswith('__') and key.endswith('__')):
        #        print(f"URN.{key}={value}")

        # icons for schemes are kept in a separate class for some reason
        from temba.contacts.templatetags.contacts import URN_SCHEME_ICONS
        URN_SCHEME_ICONS.update(PM_Scheme_Icons)

        from engage.orgs.bandwidth import BandwidthOrgModelOverrides
        BandwidthOrgModelOverrides.setClassOverrides()

        from engage.orgs.views.user_assign import OrgViewAssignUserMixin
        OrgViewAssignUserMixin.setClassOverrides()
        from engage.orgs.views.user_delete import UserViewDeleteOverride
        UserViewDeleteOverride.setClassOverrides()
        from engage.orgs.views.bandwidth import BandwidthChannelViewsMixin
        BandwidthChannelViewsMixin.setClassOverrides()
        from engage.orgs.views.home import HomeOverrides
        HomeOverrides.setClassOverrides()
        from engage.orgs.views.manage_orgs import AdminManageOverrides
        AdminManageOverrides.setClassOverrides()
        from engage.orgs.views.create import OrgViewCreateOverride
        OrgViewCreateOverride.setClassOverrides()
        from engage.orgs.views.resthooks import ResthooksOverrides, ResthookFormOverrides
        ResthooksOverrides.setClassOverrides()
        ResthookFormOverrides.setClassOverrides()

        # override the date picker widget with one we like better
        import smartmin.widgets
        from engage.msgs.datepicker import DatePickerMedia
        smartmin.widgets.DatePickerWidget.Media = DatePickerMedia

        from engage.msgs.models import MsgModelOverride, LabelModelOverride
        MsgModelOverride.setClassOverrides()
        LabelModelOverride.setClassOverrides()

        from engage.msgs.msgcontent import ListMsgContentMixin
        from temba.msgs.views import InboxView as BaseMsgInboxView
        BaseMsgInboxView.__bases__ = (ListMsgContentMixin,) + BaseMsgInboxView.__bases__

        from engage.msgs.inbox_msgfailed import ViewInboxFailedMsgsOverrides
        ViewInboxFailedMsgsOverrides.setClassOverrides()
        from engage.msgs.exporter import MsgExporterOverrides
        MsgExporterOverrides.setClassOverrides()

        from temba.mailroom.events import event_renderers
        from engage.mailroom.events import getHistoryContentFromMsg, getHistoryContentFromChannelEvent
        from temba.msgs.models import Msg, ChannelEvent
        event_renderers[Msg] = getHistoryContentFromMsg
        event_renderers[ChannelEvent] = getHistoryContentFromChannelEvent

        from temba.contacts.templatetags.contacts import register
        from engage.contacts.templatetags import scheme_icon
        register.filter(scheme_icon)

        from engage.contacts.models import ContactFieldOverrides
        ContactFieldOverrides.setClassOverrides()

        from engage.archives.models import ArchiveOverrides
        ArchiveOverrides.setClassOverrides()

        cls.ENGAGE_OVERRIDES_RAN = True
    #enddef RunEngageOverrides
#endclass EngageOverrides
