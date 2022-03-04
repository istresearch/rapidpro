from django import forms
from django.contrib.postgres.forms import JSONField

from temba.channels.models import Channel

class UpdateChannelFormMixin:
    # needed for added fields in Meta sub-class
    tps = forms.IntegerField(label="Maximum Transactions per Second", required=False)
    config = JSONField(required=False)

    class Meta:
        model = Channel
        fields = "name", "address", "country", "alert_email", "tps", "config"
        readonly = ()
        labels = {}
        helps = {}
