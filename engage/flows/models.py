from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.flows.models import Flow


class FlowOverrides(ClassOverrideMixinMustBeFirst, Flow):
    override_ignore = ignoreDjangoModelAttrs(Flow)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    TYPE_CHOICES = (
        (Flow.TYPE_MESSAGE, _("Messaging")),
        (Flow.TYPE_VOICE, _("Phone Call")),
        (Flow.TYPE_BACKGROUND, _("Background")),
        # (Flow.TYPE_SURVEY, _("Surveyor")), # P4-1483
    )

#endclass FlowOverrides
