from django.conf import settings

from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.models import Channel
from temba.contacts.models import URN


class ChannelOverrides(MonkeyPatcher):
    patch_class = Channel

    CONFIG_NAME_FORMAT = "name_format"
    CONFIG_CHAT_MODE = "chat_mode"
    CONFIG_PHONE_NUMBER = "phone_number"
    CONFIG_DEVICE_MODEL = "device_model"
    CONFIG_IMEI = "imei"

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
        return self.address
    #enddef device_id

    @property
    def name_format(self: Channel):
        return self.config[self.CONFIG_NAME_FORMAT] if self.CONFIG_NAME_FORMAT in self.config else ''
    #enddef name_format

    @property
    def chat_mode(self: Channel):
        return self.config[self.CONFIG_CHAT_MODE] if self.CONFIG_CHAT_MODE in self.config else ''
    #enddef chat_mode

    @property
    def children(self: Channel):
        from django.db.models.expressions import RawSQL
        return Channel.objects.annotate(
            my_chat_mode=RawSQL("config::json->>'chat_mode'", [])
        ).filter(parent=self, is_active=True).order_by('my_chat_mode')
    #enddef children

    @staticmethod
    def formatChannelName(name_format, channel: Channel, user):
        user_name = user.first_name or user.last_name or user.username
        channel_name = (
            name_format
            .replace('{{device_id}}', channel.address)
            .replace('{{pm_scheme}}', channel.schemes[0].strip('{}'))
            .replace('{{pm_mode}}', channel.config['chat_mode'] if 'chat_mode' in channel.config else '')
            .replace('{{phone_number}}', channel.config['phone_number'] if 'phone_number' in channel.config else '')
            .replace('{{org}}', user.get_org().name)
            .replace('{{first_name}}', user_name)
        )
        return channel_name
    #enddef formatChannelName

#endclass ChannelOverrides


from temba.channels.types.android.type import AndroidType
class AndroidTypeOverrides(MonkeyPatcher):
    patch_class = AndroidType
    # existing channels won't crash the system, but cannot add new channels of this type.
    beta_only = True
#endclass
