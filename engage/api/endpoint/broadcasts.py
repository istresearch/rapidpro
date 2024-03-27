from engage.utils.class_overrides import MonkeyPatcher

from temba.api.v2.views import BroadcastsEndpoint
from temba.msgs.models import Broadcast


class BroadcastsEndpointOverrides(MonkeyPatcher):
    patch_class = BroadcastsEndpoint

    @staticmethod
    def on_apply_patches(under_cls) -> None:
        # Django rest_framework API doc rendering in use is the BrowsableAPIRenderer which
        # does not allow dynamic docstrings to render variables. MonkeyPatcher to the rescue!
        under_cls.__doc__ = under_cls.__doc__.replace(
            '* **text** - the text of the message to send (string, limited to 640 characters)',
            f'* **text** - the text of the message to send (string, limited to {Broadcast.MAX_TEXT_LEN} characters)',
        ).replace(
            '* **text** - the message text (string or translations object)',
            '* **text** - a dict of strings with a key of the first org language, if defined, else "base". NOTE: the key is the [ISO-639-3](https://en.wikipedia.org/wiki/List_of_ISO_639-3_codes) code for the language.',
        ).replace(
            '"text": "hello world",',
            '"text": {"eng": "hello world"},',
        )
    #enddef on_apply_patches

#endclass BroadcastsEndpointOverrides
