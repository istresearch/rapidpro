from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.channels.models import Channel
from temba.contacts.models import URN


class ChannelOverrides(ClassOverrideMixinMustBeFirst, Channel):
    override_ignore = ignoreDjangoModelAttrs(Channel)

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
        if URN.TEL_SCHEME in schemes:
            config[Channel.CONFIG_ALLOW_INTERNATIONAL] = True
        #endif
        cls.getOrigClsAttr('create')(cls, org, user, country, channel_type, name, address, config, role, schemes, **kwargs)
    #enddef create

#endclass ChannelOverrides

from temba.channels.types.android.type import AndroidType
class AndroidTypeOverrides(ClassOverrideMixinMustBeFirst, AndroidType):
    override_ignore = ('_abc_impl',)
    # existing channels won't crash the system, but cannot add new channels of this type.
    beta_only = True
#endclass
