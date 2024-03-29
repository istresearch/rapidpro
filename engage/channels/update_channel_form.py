from django import forms
from django.forms import JSONField

from engage.utils.class_overrides import MonkeyPatcher
from temba.channels.models import Channel
from temba.channels.views import UpdateChannelForm


class UpdateChannelFormOverrides(MonkeyPatcher):
    patch_class = UpdateChannelForm

    # needed for added fields in Meta sub-class
    tps = forms.IntegerField(label="Maximum Transactions per Second", required=False)
    config = JSONField(required=False)

    class Meta:
        model = Channel
        fields = "name", "address", "country", "alert_email", "tps", "config"
        readonly = ()
        labels = {}
        helps = {}
    #endclass Meta

#endclass UpdateChannelFormOverrides
