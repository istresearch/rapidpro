import bandwidth

from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from engage.utils.bandwidth import BandwidthRestClient

from smartmin.views import (
    SmartFormView,
    SmartUpdateView,
)
from temba.orgs.models import Org
from temba.orgs.views import (
    ModalMixin,
    InferOrgMixin,
    OrgPermsMixin,
)


BW_APPLICATION_SID = "BW_APPLICATION_SID"
BW_ACCOUNT_SID = "BW_ACCOUNT_SID"
BW_ACCOUNT_TOKEN = "BW_ACCOUNT_TOKEN"
BW_ACCOUNT_SECRET = "BW_ACCOUNT_SECRET"
BW_PHONE_NUMBER = "BW_PHONE_NUMBER"
BW_API_TYPE = "BW_API_TYPE"

BWI_USERNAME = "BWI_USERNAME"
BWI_PASSWORD = "BWI_PASSWORD"
BWI_ENCODING = "BWI_ENCODING"
BWI_SENDER = "BWI_SENDER"

class BandwidthOrgModelMixin:

    def connect_bandwidth(self, account_sid, account_token, account_secret, application_sid, user):
        self.config.update({
            BW_ACCOUNT_SID: account_sid,
            BW_ACCOUNT_TOKEN: account_token,
            BW_ACCOUNT_SECRET: account_secret,
            BW_APPLICATION_SID: application_sid,
        })
        self.modified_by = user
        self.save(update_fields=("config", "modified_by", "modified_on"))

    def connect_bandwidth_international(self, username, password, user):
        """
        BWI Unsupported
        """
        pass

    def is_connected_to_bandwidth(self):
        if self.config:
            bw_account_sid = self.config.get(BW_ACCOUNT_SID, None)
            bw_account_token = self.config.get(BW_ACCOUNT_TOKEN, None)
            if bw_account_sid and bw_account_token:
                return True
        return False

    def is_connected_to_bandwidth_international(self):
        """
        BWI Unsupported
        """
        return False

    def get_bandwidth_messaging_client(self):
        if self.config:
            bw_account_sid = self.config.get(BW_ACCOUNT_SID, None)
            bw_account_token = self.config.get(BW_ACCOUNT_TOKEN, None)
            bw_account_secret = self.config.get(BW_ACCOUNT_SECRET, None)

            if bw_account_sid and bw_account_token and bw_account_secret:
                return bandwidth.client('messaging', bw_account_sid, bw_account_token, bw_account_secret)
        return None

    def get_bandwidth_international_messaging_client(self):
        """
        BWI Unsupported
        """
        return None

    def remove_bandwidth_account(self, user, international=False):
        if self.config:
            channel_type = "BWD"
            if international:
                channel_type = "BWI"

            for channel in self.channels.filter(is_active=True, channel_type__in=[channel_type]):
                channel.release()

            if channel_type == "BWI":
                self.config[BWI_USERNAME] = ""
                self.config[BWI_PASSWORD] = ""
            elif channel_type == "BWD":
                self.config[BW_ACCOUNT_SID] = ""
                self.config[BW_APPLICATION_SID] = ""
                self.config[BW_ACCOUNT_TOKEN] = ""
                self.config[BW_ACCOUNT_SECRET] = ""

            self.modified_by = user
            self.save()
    #enddef remove_bandwidth_account

#endclass BandwidthOrgModelMixin

class BandwidthChannelViewsMixin:

    @classmethod
    def get_actions(cls):
        return (
            "bandwidth_connect",
            "bandwidth_international_connect",
            "bandwidth_account",
            "bandwidth_international_account",
        )

    class BandwidthConnect(ModalMixin, InferOrgMixin, OrgPermsMixin, SmartFormView):
        class BandwidthConnectForm(forms.Form):
            bw_account_sid = forms.CharField(label="Account SID", help_text=_("Your Bandwidth Account ID"))
            bw_account_token = forms.CharField(label="Account Token", help_text=_("Your Bandwidth API Token"))
            bw_account_secret = forms.CharField(label="Account Secret", help_text=_("Your Bandwidth API Secret"),
                                                widget=forms.PasswordInput(render_value=True)
                                                )
            bw_application_sid = forms.CharField(label="Application SID", help_text=_("Your Bandwidth Account Application ID"))

            def clean(self):
                bw_account_sid = self.cleaned_data.get("bw_account_sid", None)
                bw_account_token = self.cleaned_data.get("bw_account_token", None)
                bw_account_secret = self.cleaned_data.get("bw_account_secret", None)
                bw_application_sid = self.cleaned_data.get("bw_application_sid", None)

                if not bw_account_sid:  # pragma: needs cover
                    raise ValidationError(_("You must enter your Bandwidth Account ID"))

                if not bw_account_token:
                    raise ValidationError(_("You must enter your Bandwidth Account Token"))
                if not bw_account_secret:
                    raise ValidationError(_("You must enter your Bandwidth Account Secret"))
                if not bw_application_sid:
                    raise ValidationError(_("You must enter your Bandwidth Account's Application ID"))

                bw_application_sid = forms.CharField(help_text=_("Your Bandwidth Account Application ID"))

                try:
                    client = BandwidthRestClient('{}'.format(bw_account_sid), '{}'.format(bw_account_token),
                                                 '{}'.format(bw_account_secret), bw_application_sid, client_name='account', api_version='')
                    media = client.get_media()
                except Exception:
                    raise ValidationError(
                        _("The Bandwidth account credentials seem invalid. Please check them again and retry.")
                    )

                return self.cleaned_data

        form_class = BandwidthConnectForm
        submit_button_name = "Save"
        success_url = "@channels.types.bandwidth.claim"
        field_config = dict(bw_account_sid=dict(label=""), bw_account_token=dict(label=""))
        success_message = "Bandwidth Account successfully connected."

        def form_valid(self, form):
            bw_account_sid = form.cleaned_data["bw_account_sid"]
            bw_account_token = form.cleaned_data["bw_account_token"]
            bw_account_secret = form.cleaned_data["bw_account_secret"]
            bw_application_sid = form.cleaned_data["bw_application_sid"]

            org = self.get_object()
            org.connect_bandwidth(bw_account_sid, bw_account_token, bw_account_secret,
                                  bw_application_sid, self.request.user)
            org.save()

            return HttpResponseRedirect(self.get_success_url())

    #endclass BandwidthConnect

    class BandwidthInternationalConnect(ModalMixin, InferOrgMixin, OrgPermsMixin, SmartFormView):
        class BandwidthInternationalConnectForm(forms.Form):
            bwi_username = forms.CharField(label="Username", help_text=_("Bandwidth Username"))
            bwi_password = forms.CharField(label="Password", help_text=_("Bandwidth Password"),
                                           widget=forms.PasswordInput(render_value=True)
                                           )

            def clean(self):
                bwi_username = forms.CharField(label="Username", help_text=_("Bandwidth Username"))
                bwi_password = forms.CharField(widget=forms.PasswordInput, label="Password",
                                               help_text=_("Bandwidth Password"))

                if not bwi_username:
                    raise ValidationError(_("You must enter your Bandwidth Account Username"))
                if not bwi_password:
                    raise ValidationError(_("You must enter your Bandwidth Account Password"))

                return self.cleaned_data

        form_class = BandwidthInternationalConnectForm
        submit_button_name = "Save"
        success_url = "@channels.types.bandwidth_international.claim"
        field_config = dict(bwi_username=dict(label=""), bwi_password=dict(label=""))
        success_message = "Bandwidth Account successfully connected."

        def form_valid(self, form):
            bwi_username = form.cleaned_data["bwi_username"]
            bwi_password = form.cleaned_data["bwi_password"]

            org = self.get_object()
            org.connect_bandwidth_international(bwi_username, bwi_password, self.request.user)
            org.save()

            return HttpResponseRedirect(self.get_success_url())

    #endclass BandwidthInternationalConnect

    class BandwidthAccount(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        success_message = ""
        success_url = "@orgs.org_home"

        class BandwidthKeys(forms.ModelForm):
            bw_account_sid = forms.CharField(max_length=128, label=_("Account ID"), required=False)
            bw_account_token = forms.CharField(max_length=128, label=_("Account Token"), required=False)
            bw_account_secret = forms.CharField(max_length=128, label=_("Account Secret"), required=False,
                                                widget=forms.PasswordInput(render_value=True)
                                                )
            bw_application_sid = forms.CharField(label="Application SID",
                                                 help_text=_("Your Bandwidth Account Application ID"), required=False)
            channel_id = forms.CharField(widget=forms.HiddenInput, max_length=6, required=False)
            disconnect = forms.CharField(widget=forms.HiddenInput, max_length=6, required=True)

            def clean(self):
                super().clean()
                if self.cleaned_data.get("disconnect", "false") == "false":
                    bw_account_sid = self.cleaned_data.get("bw_account_sid", None)
                    bw_account_token = self.cleaned_data.get("bw_account_token", None)
                    bw_application_sid = self.cleaned_data.get("bw_application_sid", None)
                    bw_account_secret = self.cleaned_data.get("bw_account_secret", None)

                    if not bw_account_secret:
                        raise ValidationError(_("You must enter your Bandwidth Account Secret"))

                    if not bw_account_sid:
                        raise ValidationError(_("You must enter your Bandwidth Account SID"))

                    if not bw_account_token:  # pragma: needs cover
                        raise ValidationError(_("You must enter your Bandwidth Account Token"))

                    if not bw_application_sid:
                        raise ValidationError(_("You must enter your Bandwidth Account's Application ID"))

                    try:
                        client = BandwidthRestClient('{}'.format(bw_account_sid), '{}'.format(bw_account_token),
                                                     '{}'.format(bw_account_secret),
                                                     bw_application_sid,
                                                     client_name='account', api_version='')
                        media = client.get_media()
                    except Exception:
                        raise ValidationError(
                            _("The Bandwidth account credentials seem invalid. Please check them again and retry.")
                        )

                return self.cleaned_data

            class Meta:
                model = Org
                fields = ("bw_account_sid", "bw_account_token", "bw_account_secret",
                "bw_application_sid", "channel_id", "disconnect")

        form_class = BandwidthKeys

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            client = self.object.get_bandwidth_messaging_client()
            if client:
                context[str.lower(BW_ACCOUNT_SID)] = self.org.config[BW_ACCOUNT_SID]
                context[str.lower(BW_ACCOUNT_TOKEN)] = self.org.config[BW_ACCOUNT_TOKEN]
                context[str.lower(BW_ACCOUNT_SECRET)] = self.org.config[BW_ACCOUNT_SECRET]
                context[str.lower(BW_APPLICATION_SID)] = self.org.config[BW_APPLICATION_SID]
                sid_length = len(context[str.lower(BW_ACCOUNT_SID)])
                context["account_sid"] = "%s%s" % ("\u066D" * (sid_length - 16), context[str.lower(BW_ACCOUNT_SID)][-16:])
            return context

        def derive_initial(self):
            initial = {}
            org = self.get_object()
            client = org.get_bandwidth_messaging_client()
            config = self.org.config
            if client:
                initial[str.lower(BW_ACCOUNT_SID)] = config.get(BW_ACCOUNT_SID, None)
                initial[str.lower(BW_ACCOUNT_TOKEN)] = config.get(BW_ACCOUNT_TOKEN, None)
                initial[str.lower(BW_ACCOUNT_SECRET)] = config.get(BW_ACCOUNT_SECRET, None)
                initial[str.lower(BW_APPLICATION_SID)] = config.get(BW_APPLICATION_SID, None)
            initial["disconnect"] = "false"
            return initial

        def form_valid(self, form):
            disconnect = form.cleaned_data.get("disconnect", "false") == "true"
            user = self.request.user
            org = user.get_org()

            if disconnect:
                org.remove_bandwidth_account(user)
                return HttpResponseRedirect(reverse("orgs.org_home"))
            else:
                bw_account_sid = form.cleaned_data["bw_account_sid"]
                bw_account_token = form.cleaned_data["bw_account_token"]
                bw_account_secret = form.cleaned_data["bw_account_secret"]
                bw_application_sid = form.cleaned_data["bw_application_sid"]

                org.connect_bandwidth(bw_account_sid, bw_account_token, bw_account_secret, bw_application_sid,
                                      self.request.user)
                return super().form_valid(form)

    #endclass BandwidthAccount

    class BandwidthInternationalAccount(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        success_message = ""
        success_url = "@orgs.org_home"

        class BandwidthKeys(forms.ModelForm):
            bwi_username = forms.CharField(max_length=128, label=_("Username"), required=False)
            bwi_password = forms.CharField(max_length=128, label=_("Password"), required=False,
                                           widget=forms.PasswordInput(render_value=True)
                                           )
            disconnect = forms.CharField(widget=forms.HiddenInput, max_length=6, required=True)
            channel_id = forms.CharField(widget=forms.HiddenInput, max_length=6, required=False)
            key = forms.IntegerField(widget=forms.HiddenInput, required=False)

            def clean(self):
                super().clean()
                if self.cleaned_data.get("disconnect", "false") == "false":
                    bwi_username = self.cleaned_data.get("bwi_username", None)
                    bwi_password = self.cleaned_data.get("bwi_password", None)

                    if not bwi_username:  # pragma: needs cover
                        raise ValidationError(_("You must enter your Bandwidth Username"))

                    self.cleaned_data["bwi_username"] = bwi_username
                    self.cleaned_data["bwi_password"] = bwi_password
                return self.cleaned_data

            class Meta:
                model = Org
                fields = ("bwi_username", "bwi_password", "disconnect", "key")

        form_class = BandwidthKeys

        def derive_initial(self):
            initial = super().derive_initial()
            org = self.get_object()
            bwi_username = org.config.get(BWI_USERNAME, None)
            bwi_password = org.config.get(BWI_PASSWORD, None)
            #bwi_key = os.environ.get("BWI_KEY")
            initial[str.lower(BWI_USERNAME)] = str.lower(bwi_username) #AESCipher(bwi_username, bwi_key).decrypt()
            initial[str.lower(BWI_PASSWORD)] = str.lower('BWI NOT AVAILABLE') #AESCipher(bwi_password, bwi_key).decrypt()
            initial["disconnect"] = bool(self.request.POST.get("disconnect"))
            return initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            org = self.get_object()
            bwi_username = org.config.get(BWI_USERNAME, None)
            bwi_password = org.config.get(BWI_PASSWORD, None)
            #bwi_key = os.environ.get("BWI_KEY")
            context[str.lower(BWI_USERNAME)] = str.lower(bwi_username) #AESCipher(bwi_username, bwi_key).decrypt()
            context[str.lower(BWI_PASSWORD)] = str.lower('BWI NOT AVAILABLE') #AESCipher(bwi_password, bwi_key).decrypt()
            return context

        def form_valid(self, form):
            disconnect = form.cleaned_data.get("disconnect", "false") == "true"
            user = self.request.user
            org = user.get_org()
            if disconnect:
                org.remove_bandwidth_account(user=user, international=True)
                return HttpResponseRedirect(reverse("orgs.org_home"))
            else:
                bwi_username = form.cleaned_data["bwi_username"]
                bwi_password = form.cleaned_data["bwi_password"]
                org.connect_bandwidth_international(bwi_username, bwi_password, self.request.user)

            response = self.render_to_response(self.get_context_data(form=form))
            response['REDIRECT'] = self.get_success_url()
            return response

    #endclass BandwidthInternationalAccount

#endclass BandwidthChannelViewsMixin
