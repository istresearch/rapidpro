from engage.utils.class_overrides import MonkeyPatcher

from temba.api.v2.views import MessagesEndpoint


class MessagesEndpointOverrides(MonkeyPatcher):
    patch_class = MessagesEndpoint

    @staticmethod
    def on_apply_patches(under_cls) -> None:
        # Django rest_framework API doc rendering in use is the BrowsableAPIRenderer which
        # does not allow dynamic docstrings to render variables. MonkeyPatcher to the rescue!
        under_cls.__doc__ = under_cls.__doc__.replace(
            '* **sent_on** - for outgoing messages, when the channel sent the message (null if not yet sent or an incoming message) (datetime).',
            f"* **sent_on** - for outgoing messages, when the channel sent the message (null if not yet sent); for incoming messages, non-null if known (datetime).",
        )
    #enddef on_apply_patches

#endclass MessagesEndpointOverrides
