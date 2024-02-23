from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from temba.flows.models import Flow
from temba.flows.views import FlowCRUDL
from temba.utils.fields import (
    SelectWidget,
)


class CreateFlowOverrides(MonkeyPatcher):
    patch_class = FlowCRUDL.Create

    def on_apply_patches(self):
        FlowCRUDL.Create.Form.flow_channels = forms.ChoiceField(
            label=_("Use Specific Channels"),
            help_text=_("Choose the channels for your flow"),
            choices=settings.CHAT_MODE_CHOICES,
            widget=SelectWidget(attrs={"widget_only": False}),
        )
    #enddef on_apply_patches

    def save(self, obj):
        self.object = Flow.create(
            self.request.org,
            self.request.user,
            obj.name,
            flow_type=obj.flow_type,
            expires_after_minutes=Flow.EXPIRES_DEFAULTS[obj.flow_type],
            base_language=obj.base_language,
            create_revision=True,
            ignore_triggers=True,
            metadata={'channels': []},
        )
    #enddef save

#endclass CreateFlowOverrides
