from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.types.twitter.views import UpdateForm


class TwitterUpdateFormMetaOverrides(ClassOverrideMixinMustBeFirst, UpdateForm.Meta):
    fields = "name", "address", "alert_email", "tps"
#endclass TwitterUpdateFormMetaOverrides
