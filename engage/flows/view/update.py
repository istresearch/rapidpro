from engage.flows.view.forms import FlowChannelsFormMixin
from engage.utils.class_overrides import MonkeyPatcher

from temba.flows.models import Flow
from temba.flows.views import FlowCRUDL
from temba.utils.fields import (
    CheckboxWidget, InputWidget,
)


class FlowViewUpdate(MonkeyPatcher):
    patch_class = FlowCRUDL.Update

    class UpdateFlowMsgForm(FlowChannelsFormMixin, FlowCRUDL.Update.MessagingForm):
        flow_channels = FlowChannelsFormMixin.flow_channels

        class Meta:
            model = Flow
            fields = ("name", "keyword_triggers", "expires_after_minutes", "ignore_triggers", "flow_channels")
            widgets = {"name": InputWidget(), "ignore_triggers": CheckboxWidget()}
        #endclass Meta
    #endclass UpdateFlowMsgForm

    class UpdateFlowIvrForm(FlowChannelsFormMixin, FlowCRUDL.Update.VoiceForm):
        flow_channels = FlowChannelsFormMixin.flow_channels

        class Meta:
            model = Flow
            fields = ("name", "keyword_triggers", "expires_after_minutes", "ignore_triggers", "ivr_retry", "flow_channels")
            widgets = {"name": InputWidget(), "ignore_triggers": CheckboxWidget()}
        #endclass Meta
    #endclass UpdateFlowIvrForm

    form_classes = {
        Flow.TYPE_MESSAGE: UpdateFlowMsgForm,
        Flow.TYPE_VOICE: UpdateFlowIvrForm,
        Flow.TYPE_SURVEY: FlowCRUDL.Update.SurveyForm,
        Flow.TYPE_BACKGROUND: FlowCRUDL.Update.BaseForm,
    }

    def pre_save(self, obj):
        obj = self.Update_pre_save(obj)
        metadata = obj.metadata

        if "flow_channels" in self.form.cleaned_data:
            metadata['channels'] = self.form.cleaned_data["flow_channels"]

        obj.metadata = metadata
        return obj
    #enddef pre_save

#endclass FlowViewUpdate
