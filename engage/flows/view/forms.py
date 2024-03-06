from django import forms
from django.utils.translation import gettext_lazy as _

from temba.channels.models import Channel


class FlowChannelsFormMixin:

    flow_schemes = forms.MultipleChoiceField(
        label=_("Channel Schemes"),
        #help_text=_("?"),
        choices=('CHANGE_ME', '1'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    flow_channels = forms.MultipleChoiceField(
        label=_("Use Specific Channels"),
        #help_text=_("Choose the channels for your flow"),
        choices=('CHANGE_ME', '1'),
        widget=forms.CheckboxSelectMultiple(),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['flow_channels'].choices = (
            Channel.objects.filter(is_active=True, org=self.org).order_by('schemes', 'name').values_list('uuid', 'name')
        )
        if self.instance:
            metadata = self.instance.metadata
            self.fields['flow_channels'].initial = metadata.get("channels", self.fields["flow_channels"].initial)
        #endif

        channel_schemes = Channel.objects.filter(is_active=True, org=self.org).order_by('uuid', 'schemes').values_list('uuid', 'schemes')
        schemes_to_filter = {}
        for uuid, schemes in channel_schemes:
            theScheme = schemes[0]
            if theScheme in schemes_to_filter:
                schemes_to_filter[theScheme] += [uuid]
            else:
                schemes_to_filter[theScheme] = [uuid]
            #endif
        #endfor
        scheme_choices = [ ( ",".join(x for x in schemes_to_filter[uuid]), uuid ) for uuid in schemes_to_filter ]
        scheme_choices.sort(key=lambda tup: tup[1])
        self.fields['flow_schemes'].choices = scheme_choices
    #enddef init

#endclass FlowChannelsFormMixin
