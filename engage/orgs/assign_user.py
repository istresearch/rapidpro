import logging

from django import forms
from django.contrib import messages
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

from engage.utils.logs import OrgPermLogInfoMixin

from smartmin.views import (
    SmartFormView,
)

from temba.api.models import APIToken
from temba.orgs.models import Org, OrgRole
from temba.orgs.views import OrgPermsMixin


logger = logging.getLogger(__name__)

class AssignUserMixin:

    class AssignUser(OrgPermLogInfoMixin, OrgPermsMixin, SmartFormView):
        permission = "orgs.org_manage_accounts"

        def has_permission(self, request, *args, **kwargs):
            user = request.user
            if user.is_authenticated:
                if user.has_perm(self.permission):
                    return True
                org = user.get_org()
                if org is not None:
                    return user.has_org_perm(org, self.permission)
            return False

        class AssignUserForm(forms.Form):
            user = None
            organization = forms.ModelChoiceField(
                queryset=Org.objects.all().order_by("name", "slug"),
                required=True,
                empty_label=None,
            )
            user_group = forms.ChoiceField(
                choices=(
                    (OrgRole.ADMINISTRATOR.code, OrgRole.ADMINISTRATOR.display),
                    (OrgRole.EDITOR.code, OrgRole.EDITOR.display),
                    (OrgRole.VIEWER.code, OrgRole.VIEWER.display),
                    (OrgRole.SURVEYOR.code, OrgRole.SURVEYOR.display),
                ),
                required=True,
                initial=OrgRole.EDITOR.code,
                label=_("Role"),
            )
            username = forms.CharField(required=True, label=_("Username"))

            def __init__(self, user, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self.user = user
                #self.organization.choices = self.user.get_user_orgs() ### O.o "'AssignUserForm' object has no attribute 'organization'"
                self.fields['organization'].choices = self.user.get_user_orgs()

            # do not need the conversion of org_pk choice to Org class when using ModelChoiceField() type of form field.
            # def clean_organization(self):
            #     org = None
            #     org_pk = self.data.get("organization")
            #     if org_pk:
            #         org = Org.objects.filter(id=org_pk).first()
            #     return org

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            kwargs["user"] = self.request.user
            return kwargs

        form_class = AssignUserForm
        title = _("Assign User to Organization")
        fields = ("organization", "user_group", "username")
        success_url = "@orgs.org_assign_user"
        success_message = ""
        submit_button_name = _("Assign User")

        def form_valid(self, form):
            org = form.cleaned_data["organization"]
            user_group = form.cleaned_data["user_group"]
            username = form.cleaned_data["username"]
            user = User.objects.filter(username__iexact=username).first() if username else None

            if org and user:
                if user_group == OrgRole.ADMINISTRATOR.code:
                    role = OrgRole.ADMINISTRATOR
                elif user_group == OrgRole.EDITOR.code:
                    role = OrgRole.EDITOR
                elif user_group == OrgRole.SURVEYOR.code:
                    role = OrgRole.SURVEYOR
                else:
                    role = OrgRole.VIEWER
                org.add_user(user=user, role=role)

                # when a user's role changes, delete any API tokens they're no longer allowed to have
                api_roles = APIToken.get_allowed_roles(org, user)
                for token in APIToken.objects.filter(org=org, user=user).exclude(role__in=api_roles):
                    token.release()

                org.save()
                logger.error("user assigned to org", extra=self.withLogInfo({
                    'assigned_to_org_uuid': org.uuid,
                    'assigned_to_org_slug': org.slug,
                    'assigned_user_id': user.id,
                    'assigned_user_name': user.username,
                    'assigned_user_email': user.email,
                    'assigned_role': role.display,
                }))
                messages.success(self.request, _("User '{}' successfully added to org '{}' as the role {}.").format(
                    user.email, org.name, role.display)
                )
            else:
                if not org:
                    theOrgPK = form.data.get("organization")
                    logger.error("org not found", extra=self.withLogInfo({
                        'assigned_org_pk': theOrgPK,
                    }))
                    messages.error(self.request, _("Org id [{}] not found.").format(theOrgPK))
                if not user:
                    theName = form.data.get("username")
                    logger.error("assigned_user not found", extra=self.withLogInfo({
                        'assigned_user': theName,
                    }))
                    messages.warning(self.request, _("Username/Email '{}' not found.").format(theName))

            success_url = reverse("orgs.org_assign_user")
            return HttpResponseRedirect(success_url)
