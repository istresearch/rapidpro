import phonenumbers

from django import forms
from django.utils.translation import gettext_lazy as _

from temba.channels.models import Channel
from temba.channels.views import ALL_COUNTRIES, AuthenticatedExternalClaimView, ClaimViewMixin
from temba.utils.fields import SelectWidget


class ClaimView(AuthenticatedExternalClaimView):
    class ClickatellForm(ClaimViewMixin.Form):
        country = forms.ChoiceField(
            choices=ALL_COUNTRIES,
            widget=SelectWidget(attrs={"searchable": True}),
            label=_("Country"),
            help_text=_("The country this phone number is used in"),
        )
        number = forms.CharField(
            max_length=18,
            min_length=1,
            label=_("Number"),
            help_text=_(
                "The phone number with country code or short code you are connecting. ex: +250788123124 or 15543"
            ),
        )
        api_key = forms.CharField(
            label=_("API Key"), help_text=_("The API key for your integration as provided by Clickatell")
        )

        def clean_number(self):
            # if this is a long number, try to normalize it
            number = self.data["number"]
            if len(number) >= 8:
                try:
                    cleaned = phonenumbers.parse(number, self.data["country"])
                    return phonenumbers.format_number(cleaned, phonenumbers.PhoneNumberFormat.E164)
                except Exception:  # pragma: needs cover
                    raise forms.ValidationError(
                        _("Invalid phone number, please include the country code. ex: +250788123123")
                    )
            else:  # pragma: needs cover
                return number

    form_class = ClickatellForm

    def form_valid(self, form):
        org = self.request.user.get_org()

        data = form.cleaned_data
        self.object = Channel.add_config_external_channel(
            org,
            self.request.user,
            data["country"],
            data["number"],
            self.channel_type,
            {Channel.CONFIG_API_KEY: data["api_key"]},
        )

        return super(AuthenticatedExternalClaimView, self).form_valid(form)
