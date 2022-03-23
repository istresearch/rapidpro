from django import forms
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

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

class PostmasterChannelMixin:

    class PostmasterAccount(InferOrgMixin, OrgPermsMixin, SmartUpdateView):
        success_message = ""

        class PostmasterKeys(forms.ModelForm):
            receiver_id = forms.CharField(label="Device ID", help_text=_("Your Postmaster Device ID"))
            chat_mode = forms.CharField(label="Chat Mode", help_text=_("Your Postmaster Chat Mode"))
            disconnect = forms.CharField(widget=forms.HiddenInput, max_length=6, required=True)

            def clean(self):
                super().clean()
                if self.cleaned_data.get("disconnect", "false") == "false":
                    receiver_id = self.cleaned_data.get("receiver_id", None)
                    chat_mode = self.cleaned_data.get("chat_mode", None)

                    if not receiver_id:
                        raise ValidationError(_("You must enter your Postmaster Device ID"))

                    if not chat_mode:  # pragma: needs cover
                        raise ValidationError(_("You must enter your Postmaster Chat Mode"))

                return self.cleaned_data

            class Meta:
                model = Org
                fields = ("receiver_id", "chat_mode", "disconnect")

        form_class = PostmasterKeys

        def derive_initial(self):
            initial = super().derive_initial()
            org = self.get_object()
            config = org.config
            initial["receiver_id"] = config.get(Org.CONFIG_POSTMASTER_RECEIVER_ID, "")
            initial["chat_mode"] = config.get(Org.CONFIG_POSTMASTER_CHAT_MODE, "")
            initial["disconnect"] = "false"
            return initial

        def form_valid(self, form):
            disconnect = form.cleaned_data.get("disconnect", "false") == "true"
            user = self.request.user
            org = user.get_org()

            if disconnect:
                org.remove_postmaster_account(user)
                return HttpResponseRedirect(reverse("orgs.org_home"))
            else:
                receiver_id = form.cleaned_data["receiver_id"]
                chat_mode = form.cleaned_data["api_secret"]

                org.connect_nexmo(receiver_id, chat_mode, user)
                return super().form_valid(form)

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)

            org = self.get_object()
            client = org.get_nexmo_client()
            if client:
                config = org.config
                context["receiver_id"] = config.get(Org.CONFIG_POSTMASTER_RECEIVER_ID, "")
                context["chat_mode"] = config.get(Org.CONFIG_POSTMASTER_CHAT_MODE, "")

            return context

    class PostmasterConnect(ModalMixin, InferOrgMixin, OrgPermsMixin, SmartFormView):
        class PostmasterConnectForm(forms.Form):
            receiver_id = forms.CharField(label="Device ID", help_text=_("Your Postmaster Device ID"))
            chat_mode = forms.CharField(label="Chat Mode", help_text=_("Your Postmaster Chat Mode"))

            def clean(self):
                receiver_id = self.cleaned_data.get("receiver_id", None)
                chat_mode = self.cleaned_data.get("chat_mode", None)

                if not receiver_id:
                    raise ValidationError(_("You must enter your Postmaster Device ID"))

                if not chat_mode:
                    raise ValidationError(_("You must enter your Postmaster Chat Mode"))

                return self.cleaned_data

        form_class = PostmasterConnectForm
        submit_button_name = "Save"
        success_url = "@channels.types.postmaster.claim"
        field_config = dict(receiver_id=dict(label=""), chat_mode=dict(label=""))
        success_message = "Postmaster Account successfully connected."

        def form_valid(self, form):
            receiver_id = form.cleaned_data["receiver_id"]
            chat_mode = form.cleaned_data["chat_mode"]

            org = self.get_object()
            org.connect_postmaster(receiver_id, chat_mode, self.request.user)
            org.save()

            return HttpResponseRedirect(self.get_success_url())
