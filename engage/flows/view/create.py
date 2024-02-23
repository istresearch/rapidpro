from engage.flows.view.forms import FlowChannelsFormMixin
from engage.utils.class_overrides import MonkeyPatcher

from temba.flows.models import Flow
from temba.flows.views import FlowCRUDL
from temba.utils.fields import (
    CheckboxWidget, InputWidget,
)


class FlowViewCreate(MonkeyPatcher):
    patch_class = FlowCRUDL.Create

    class CreateFlowForm(FlowChannelsFormMixin, FlowCRUDL.Create.Form):

        # Tricky to include this as the "default" changes based on Flow type which is another widget
        # expires_after_minutes = forms.ChoiceField(
        #     label=_("Expire inactive contacts"),
        #     help_text=_("When inactive contacts should be removed from the flow"),
        #     initial=Flow.EXPIRES_DEFAULTS[Flow.TYPE_MESSAGE],
        #     choices=Flow.EXPIRES_CHOICES[Flow.TYPE_MESSAGE],
        #     widget=SelectWidget(attrs={"widget_only": False}),
        # )

        flow_channels = FlowChannelsFormMixin.flow_channels

        class Meta:
            model = Flow
            fields = ("name", "flow_type",
                "keyword_triggers",
                "base_language", # "expires_after_minutes",
                "ignore_triggers",
                "flow_channels",
            )
            widgets = {
                "name": InputWidget(),
                "ignore_triggers": CheckboxWidget(attrs={'checked': 'checked'}),  # default to Checked/True
            }
        #endclass Meta

    #endclass CreateFlowForm

    form_class = CreateFlowForm

    def save(self: type(FlowCRUDL.Create), obj):
        if 'expires_after_minutes' in self.CreateFlowForm.Meta.fields:
            expire_contacts_timing = obj.expires_after_minutes
        else:
            expire_contacts_timing = Flow.EXPIRES_DEFAULTS[obj.flow_type]
        #endif
        self.object = Flow.create(
            self.request.org,
            self.request.user,
            obj.name,
            flow_type=obj.flow_type,
            expires_after_minutes=expire_contacts_timing,
            base_language=obj.base_language,
            create_revision=True,
            ignore_triggers=obj.ignore_triggers,
            metadata={'channels': self.form.cleaned_data["flow_channels"]},
        )
    #enddef save

#endclass FlowViewCreate
