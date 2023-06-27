from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.channels.types.viber_public.views import UpdateForm


class ViberPublicUpdateFormMetaOverrides(ClassOverrideMixinMustBeFirst, UpdateForm.Meta):
    fields = "name", "address", "alert_email", "tps"
#endclass ViberPublicUpdateFormMetaOverrides
