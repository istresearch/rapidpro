from django.conf import settings

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.channels.models import Channel
from temba.contacts.models import URN


class ChannelOverrides(ClassOverrideMixinMustBeFirst, Channel):
    override_ignore = ignoreDjangoModelAttrs(Channel)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    CONFIG_DEVICE_ID = "device_id"
    CONFIG_DEVICE_NAME = "device_name"
    CONFIG_CHAT_MODE = "chat_mode"
    CONFIG_CLAIM_CODE = "claim_code"
    CONFIG_ORG_ID = "org_id"

    @classmethod
    def create(
            cls,
            org,
            user,
            country,
            channel_type,
            name=None,
            address=None,
            config=None,
            role=Channel.DEFAULT_ROLE,
            schemes=None,
            **kwargs,
    ):
        if config is None:
            config = {}
        #endif
        # P4-3462
        if schemes and URN.TEL_SCHEME in schemes:
            config[Channel.CONFIG_ALLOW_INTERNATIONAL] = True
        #endif

        tps = getattr(settings, "DEFAULT", 10)

        return cls.getOrigClsAttr('create')(org, user, country, channel_type,
                name, address, config, role, schemes, tps, **kwargs
        )
    #enddef create

    def claim(self, org, user, phone):
        # NOTE: leaving alert_email field empty, which is the user.email param.
        user.email = None
        return self.getOrigClsAttr('claim')(self, org, user, phone)
    #enddef claim

    def release(self, user, trigger_sync: bool = True, check_dependent_flows=True, **kwargs):
        if check_dependent_flows:
            dependent_flows_count = self.dependent_flows.count()
            if dependent_flows_count > 0:
                raise ValueError(f"Cannot delete Channel: {self.get_name()}, used by {dependent_flows_count} flows")
            #endif
        #endif
        return self.getOrigClsAttr('release')(self, user, trigger_sync, **kwargs)
    #enddef release

#endclass ChannelOverrides


from temba.channels.types.android.type import AndroidType
class AndroidTypeOverrides(ClassOverrideMixinMustBeFirst, AndroidType):
    override_ignore = ('_abc_impl',)
    # existing channels won't crash the system, but cannot add new channels of this type.
    beta_only = True
#endclass
