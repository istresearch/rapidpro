from django import forms
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponseRedirect
from django.utils.translation import gettext_lazy as _

from temba.orgs.views import (
    OrgCRUDL,
    InferOrgMixin,
    OrgPermsMixin,
    SmartFormView,
)

from engage.utils.class_overrides import MonkeyPatcher


class OrgViewOverrides(MonkeyPatcher):
    patch_class = OrgCRUDL

    @staticmethod
    def on_apply_patches(under_cls) -> None:
        under_cls.actions += ('mutual_auth_config',)
    #enddef on_apply_patches

    class MutualAuthConfig(InferOrgMixin, OrgPermsMixin, SmartFormView):

        class MyForm(forms.Form):
            mauth_enabled = forms.ChoiceField(
                choices=(
                    (0, 'Disabled'),
                    (1, 'Enabled'),
                ),
                initial=0,
                label=_("Enforce mutual authentication."),
            )
        #endclass MyForm

        permission = "orgs.org_edit"
        title = _("Mutual Authentication")
        success_message = ""
        form_class = MyForm
        fields = ("mauth_enabled",)

        def __init__(self, *args):
            super().__init__(args)
            self.user = None
            self.org = None
        #enddef init

        def has_permission(self, request, *args, **kwargs):
            self.user = self.request.user
            self.org = self.request.user.get_org()
            return self.request.user.has_perm(self.permission) or self.has_org_perm(self.permission)
        #enddef has_permission

        def derive_initial(self):
            initial = super().derive_initial()
            if self.org and self.org.config:
                initial["mauth_enabled"] = self.org.config.get('mauth_enabled', 0)
            #endif
            return initial
        #enddef derive_initial

        def get_context_data(self, **kwargs):
            context = super().get_context_data(**kwargs)
            if self.org and self.org.config:
                context["mauth_enabled"] = self.org.config.get('mauth_enabled', 0)
            #endif
            return context
        #enddef get_context_data

        def form_valid(self, form):
            try:
                self.org.config.update({'mauth_enabled': int(form.cleaned_data["mauth_enabled"])})
                self.org.modified_by = self.user
                self.org.save(update_fields=("config", "modified_by", "modified_on"))

                messages.success(self.request, self.derive_success_message())
                if "HTTP_X_FORMAX" not in self.request.META:
                    return HttpResponseRedirect(self.get_success_url())
                else:
                    response = self.render_to_response(self.get_context_data(form=form))
                    response["REDIRECT"] = self.get_success_url()
                    return response
                #endif
            except IntegrityError as e:
                message = str(e).capitalize()
                form.errors.append(message)
                return self.render_to_response(self.get_context_data(form=form))
            #endtry
        #enddef form_valid

    #endclass MutualAuthConfig

#endclass OrgViewOverrides
