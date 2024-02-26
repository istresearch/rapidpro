from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from temba.channels.models import Channel


class FlowChannelsFormMixin:

    flow_channels = forms.MultipleChoiceField(
        label=_("Use Specific Channels"),
        #help_text=_("Choose the channels for your flow"),
        choices=settings.CHAT_MODE_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flow_channels'].choices = (
            Channel.objects.filter(is_active=True, org=self.org).order_by('name').values_list('uuid', 'name')
        )
        if self.instance:
            metadata = self.instance.metadata
            self.fields['flow_channels'].initial = metadata.get("channels", self.fields["flow_channels"].initial)
        #endif
    #enddef init

#endclass FlowChannelsFormMixin
