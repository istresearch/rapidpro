import logging

from django import forms
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst
from engage.utils.logs import OrgPermLogInfoMixin

from smartmin.views import (
    SmartFormView,
)

from temba.api.models import APIToken
from temba.orgs.models import Org, OrgRole, User
from temba.orgs.views import OrgPermsMixin, OrgCRUDL


logger = logging.getLogger(__name__)

class OrgViewAssignUserMixin(ClassOverrideMixinMustBeFirst, OrgCRUDL):

    @staticmethod
    def on_apply_overrides(under_cls) -> None:
        under_cls.actions += ('assign_user',)
    #enddef on_apply_overrides

    class AssignUser(OrgPermLogInfoMixin, OrgPermsMixin, SmartFormView):
        permission = "orgs.org_manage_accounts"

        def as_json(self, context):
            pass

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
                queryset=Org.objects.all(),
                required=True,
                label=_("Workspace"),
                empty_label=_("Choose Workspace"),
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
                self.fields['organization'].choices = self.get_org_choices()
            #enddef init

            def get_org_choices(self):
                admin_orgs = OrgRole.ADMINISTRATOR.get_orgs(self.user)
                return admin_orgs.filter(is_active=True).distinct().order_by("name", "slug")
            #enddef get_org_choices

            # do not need the conversion of org_pk choice to Org class when using ModelChoiceField() type of form field.
            # def clean_organization(self):
            #     org = None
            #     org_pk = self.data.get("organization")
            #     if org_pk:
            #         org = Org.objects.filter(id=org_pk).first()
            #     return org
        #endclass AssignUserForm

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            kwargs["user"] = self.request.user
            return kwargs
        #enddef get_form_kwargs

        form_class = AssignUserForm
        title = _("Assign User to Organization")
        fields = ("organization", "user_group", "username")
        success_url = "@orgs.org_assign_user"
        success_message = ""
        submit_button_name = _("Assign User")

        def assign_user(self, org, role, user):
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
            messages.success(self.request,
                _("User '{}' successfully added to org '{}' as the role {}.").format(
                    user.email, org.name, role.display
                )
            )
        #enddef assign_user

        def form_valid(self, form):
            org = form.cleaned_data["organization"]
            if org:
                user_group = form.cleaned_data["user_group"]
                role = OrgRole.from_code(user_group)
                if role:
                    username = form.cleaned_data["username"]
                    user = User.objects.filter(username__iexact=username).first() if username else None
                    if user:
                        if user.id != self.get_user().id:
                            self.assign_user(org, role, user)
                        else:
                            logger.warning("assigned_user cannot be self", extra=self.withLogInfo({
                                'assigned_user': self.get_user().username,
                            }))
                            messages.warning(self.request, _("You cannot re-assign yourself."))
                    else:
                        theName = form.data.get("username")
                        logger.error("assigned_user not found", extra=self.withLogInfo({
                            'assigned_user': theName,
                        }))
                        messages.warning(self.request, _("Username/Email '{}' not found.").format(theName))
                else:
                    theRole = user_group
                    logger.error("role not found", extra=self.withLogInfo({
                        'assigned_role': theRole,
                    }))
                    messages.error(self.request, _("Role '{}' not found.").format(theRole))
            else:
                theOrgPK = form.data.get("organization")
                logger.error("org not found", extra=self.withLogInfo({
                    'assigned_org_pk': theOrgPK,
                }))
                messages.error(self.request, _("Org id [{}] not found.").format(theOrgPK))

            success_url = reverse("orgs.org_assign_user")
            return HttpResponseRedirect(success_url)
        #enddef form_valid
    #endclass AssignUser

#endclass OrgViewAssignUserMixin
