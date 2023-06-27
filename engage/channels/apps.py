from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.channels"
    label = "engage_channels"
    verbose_name = "Engage Channels"

    @staticmethod
    def _add_pm_types():
        from temba.contacts.models import URN as TembaURN
        from .types.postmaster.schemes import PM_Schemes, PM_Scheme_Labels, PM_Scheme_Icons

        # Sort PM schemes alphabetically
        Processed_TembaURN_Scheme_Choices = TembaURN.SCHEME_CHOICES + \
            tuple([t[1] for t in sorted((lambda x: [[y[1].split(" ")[1], y] for y in x])(PM_Scheme_Labels))])

        # URN is a static-only class, add in our needs
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
    #enddef

    def ready(self):
        self._add_pm_types()

        from .models import ChannelOverrides, AndroidTypeOverrides
        ChannelOverrides.setClassOverrides()
        AndroidTypeOverrides.setClassOverrides()

        from .types.telegram.type import TelegramTypeOverrides
        TelegramTypeOverrides.setClassOverrides()

        from .types.twilio.type import TwilioTypeOverrides
        TwilioTypeOverrides.setClassOverrides()

        from .types.twitter.views import TwitterUpdateFormMetaOverrides
        TwitterUpdateFormMetaOverrides.setClassOverrides()

        from .types.viber_public.views import ViberPublicUpdateFormMetaOverrides
        ViberPublicUpdateFormMetaOverrides.setClassOverrides()

        from .types.vonage_client import VonageClientOverrides
        VonageClientOverrides.setClassOverrides()

        from .types.vonage_views import ClaimViewOverrides
        ClaimViewOverrides.setClassOverrides()

        from .update_channel_form import UpdateChannelFormOverrides
        UpdateChannelFormOverrides.setClassOverrides()

        from .views import ChannelCRUDLOverrides
        ChannelCRUDLOverrides.setClassOverrides()

        from .views import ChannelReadOverrides
        ChannelReadOverrides.setClassOverrides()

        from .views import ChannelClaimOverrides
        ChannelClaimOverrides.setClassOverrides()

        from .views import ChannelClaimAllOverrides
        ChannelClaimAllOverrides.setClassOverrides()

        from .views import ChannelDeleteOverrides
        ChannelDeleteOverrides.setClassOverrides()

        from .views import ChannelUpdateOverrides
        ChannelUpdateOverrides.setClassOverrides()

        from .views import ChannelListOverrides
        ChannelListOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
