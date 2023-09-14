from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.types.viber_public.views import UpdateForm


class ViberPublicUpdateFormMetaOverrides(MonkeyPatcher):
    patch_class = UpdateForm.Meta
    fields = "name", "address", "alert_email", "tps"
#endclass ViberPublicUpdateFormMetaOverrides
