from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from temba.channels.types.postmaster.views import ClaimView
from temba.contacts.models import URN

from .. import TYPES

from ...models import ChannelType, Channel
from ...views import UpdateChannelForm


class UpdatePostmasterForm(UpdateChannelForm):
    CHAT_MODE_CHOICES = getattr(settings, "CHAT_MODE_CHOICES", ())

    def __init__(self, *args, **kwargs):
        super(UpdatePostmasterForm, self).__init__(*args, **kwargs)

    class Meta(UpdateChannelForm.Meta):
        fields = "name", "address", "schemes", "tps"
        readonly = ("address", "schemes")
        helps = {"schemes": _("The Chat Mode that Postmaster will operate under.")}
        labels = {"schemes": _("Chat Mode")}

        from temba.channels.types.postmaster.views import ClaimView as ClaimView
        prefix = 'PM_'
        chat_mode_choices = []
        for value, label in ClaimView.Form.CHAT_MODE_CHOICES:
            if value == 'SMS':
                prefix = ''
            chat_mode_choices.append(('{}{}'.format(prefix, label).lower(), label))
        chat_mode_choices = tuple(chat_mode_choices)

    def clean(self):
        self._validate_unique = True
        config = self.object.config
        scheme = None
        if hasattr(self.cleaned_data, 'scheme'):
            scheme = self.cleaned_data['schemes'][0]
        channel = self.object
        if channel.org is not None and scheme is not None:
            channels = Channel.objects.filter(channel_type=ClaimView.code, is_active=True, address=config['device_id'])
            for ch in channels:
                if ch.config.get('chat_mode') == scheme and ch.org.id == channel.org.id:
                    if ch.__eq__(channel):
                        break
                    else:
                        raise ValidationError(_("A chat mode for {} already exists for the {} org".
                                                format(scheme, channel.org.name)))
                    break

        return self.cleaned_data

    def save(self, commit=True):
        config = self.object.config

        if hasattr(self.cleaned_data, 'schemes'):
            config[Channel.CONFIG_CHAT_MODE] = self.cleaned_data['schemes'][0]

        import temba.contacts.models as Contacts
        prefix = 'PM_'
        pm_chat_mode = config['chat_mode']

        if len(pm_chat_mode.split('pm_')) > 1:
            pm_chat_mode = pm_chat_mode.split('pm_')[1]
            for value, label in ClaimView.Form.CHAT_MODE_CHOICES:
                if label.lower() == pm_chat_mode:
                    pm_chat_mode = value

        if pm_chat_mode.upper() == 'SMS':
            pm_chat_mode = 'SMS'
            prefix = ''

        schemes = [getattr(URN,
                           '{}{}_SCHEME'.format(prefix, dict(ClaimView.Form.CHAT_MODE_CHOICES)[pm_chat_mode]).upper())]
        self.object.schemes = schemes
        return super().save(commit=commit)


class PostmasterType(ChannelType):
    """
    An IST Postmaster channel
    """

    code = "PSM"
    category = ChannelType.Category.PHONE

    courier_url = r"^psms/(?P<uuid>[a-z0-9\-]+)/(?P<action>receive|status)$"

    name = "Postmaster"
    icon = "icon-tembatoo-postmaster"
    claim_blurb = _(
        """Use Postmaster compatible android devices with Pulse Engage"""
    )
    claim_view = ClaimView

    show_config_page = False

    schemes = None
    _scheme = schemes
    max_length = 1600

    update_form = UpdatePostmasterForm

    def deactivate(self, channel):
        number_update_args = dict()

        if not channel.is_delegate_sender():
            number_update_args["sms_application_sid"] = ""

        if channel.supports_ivr():
            number_update_args["voice_application_sid"] = ""

    @property
    def schemes(self):
        for type in TYPES:
            if self._scheme is not None and type.name.lower() == self._scheme.lower():
                self.update_form = UpdatePostmasterForm
        return self._scheme

    @schemes.setter
    def set_schemes(self, value):
        self.schemes = _scheme = value

