from engage.utils.class_overrides import MonkeyPatcher

from temba.api.v2.views import ContactsEndpoint


class ContactsEndpointOverrides(MonkeyPatcher):
    patch_class = ContactsEndpoint

    @staticmethod
    def on_apply_patches(under_cls) -> None:
        # Django rest_framework API doc rendering in use is the BrowsableAPIRenderer which
        # does not allow dynamic docstrings to render variables. MonkeyPatcher to the rescue!
        under_cls.__doc__ = under_cls.__doc__.replace(
            '* **groups**',
            f"* **channels** - the contact's set channels by URN\n     * **groups**",
        )
    #enddef on_apply_patches

#endclass ContactsEndpointOverrides
