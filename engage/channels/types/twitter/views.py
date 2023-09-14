from engage.utils.class_overrides import MonkeyPatcher

from temba.channels.types.twitter.views import UpdateForm


class TwitterUpdateFormMetaOverrides(MonkeyPatcher):
    patch_class = UpdateForm.Meta
    fields = "name", "address", "alert_email", "tps"
#endclass TwitterUpdateFormMetaOverrides
