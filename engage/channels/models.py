from django.conf import settings

from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.models import Channel
from temba.contacts.models import URN


class ChannelOverrides(MonkeyPatcher):
    patch_class = Channel

    CONFIG_DEVICE_ID = "device_id"
    CONFIG_DEVICE_NAME = "device_name"
    CONFIG_CHAT_MODE = "chat_mode"
    CONFIG_CLAIM_CODE = "claim_code"
    CONFIG_ORG_ID = "org_id"

    def create(
            cls: type[Channel],
            org,
            user,
            country,
            channel_type,
            name=None,
            address=None,
            config=None,
            role=Channel.DEFAULT_ROLE,
            tps=10,
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

        tps = getattr(settings, "DEFAULT_TPS", tps)

        return cls.Channel_create(org=org, user=user, country=country, channel_type=channel_type,
                name=name, address=address, config=config, role=role, schemes=schemes, tps=tps, **kwargs
        )
    #enddef create

    def claim(self, org, user, phone):
        # NOTE: leaving alert_email field empty, which is the user.email param.
        user.email = None
        return self.Channel_claim(org=org, user=user, phone=phone)
    #enddef claim

    def release(self: Channel, user, *, trigger_sync: bool = True, check_dependent_flows: bool = True):
        if check_dependent_flows:
            dependent_flows_count = self.dependent_flows.count()
            if dependent_flows_count > 0:
                raise ValueError(f"Cannot delete Channel: {self.get_name()}, used by {dependent_flows_count} flows")
            #endif
        #endif
        return self.Channel_release(user, trigger_sync=trigger_sync)
    #enddef release

    @property
    def apps(self: Channel):
        return self.config['apps'] if 'apps' in self.config else ''
    #enddef apps

    @property
    def device_id(self: Channel):
        return self.config['device_id'] if 'device_id' in self.config else ''
    #enddef device_id

    @property
    def device_name(self: Channel):
        return self.config['device_name'] if 'device_name' in self.config else ''
    #enddef device_name

#endclass ChannelOverrides


from temba.channels.types.android.type import AndroidType
class AndroidTypeOverrides(MonkeyPatcher):
    patch_class = AndroidType
    # existing channels won't crash the system, but cannot add new channels of this type.
    beta_only = True
#endclass
