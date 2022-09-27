import logging

import pytz
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.encoding import force_str
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from smartmin.views import SmartCreateView

from temba import settings
from temba.orgs.models import Org, OrgRole
from temba.orgs.views import OrgCRUDL
from temba.utils import languages
from temba.utils.timezones import TimeZoneFormField

logger = logging.getLogger(__name__)


class OrgCreateForm(forms.ModelForm):
    first_name = forms.CharField(
        help_text=_("The first name of the workspace administrator"),
        max_length=User._meta.get_field("first_name").max_length,
    )
    last_name = forms.CharField(
        help_text=_("Your last name of the workspace administrator"),
        max_length=User._meta.get_field("last_name").max_length,
    )
    email = forms.EmailField(
        help_text=_("Their email address"), max_length=User._meta.get_field("username").max_length
    )
    timezone = TimeZoneFormField(help_text=_("The timezone for the workspace"))
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False,
        help_text=_("Their password, at least eight letters please. (leave blank for existing login)"),
    )
    name = forms.CharField(label=_("Workspace"), help_text=_("The name of the new workspace"))
    credits = forms.ChoiceField(choices=(), help_text=_("The initial number of credits granted to this workspace"))

    def __init__(self, *args, **kwargs):
        branding = kwargs["branding"]
        del kwargs["branding"]

        super().__init__(*args, **kwargs)

        welcome_packs = branding["welcome_packs"]

        choices = [(settings.ORG_PLAN_ENGAGE, 'Credits not used')]
        for pack in welcome_packs:
            choices.append((str(pack["size"]), "%d - %s" % (pack["size"], pack["name"])))

        self.fields["credits"].choices = choices
    #enddef init

    def clean(self):
        data = self.cleaned_data

        email = data.get("email", None)
        password = data.get("password", None)

        # for granting new accounts, either the email maps to an existing user (and their existing password is used)
        # or both email and password must be included
        if email:
            user = User.objects.filter(username__iexact=email).first()
            if user:
                if password:
                    raise ValidationError(_("Login already exists, please do not include password."))
            else:
                if not password:
                    raise ValidationError(_("Password required for new login."))

                validate_password(password)

        return data
    #enddef clean

    class Meta:
        model = Org
        fields = "__all__"
    #endclass Meta

#endclass OrgCreateForm

class OrgViewCreateOverride(ClassOverrideMixinMustBeFirst, OrgCRUDL):

    @staticmethod
    def on_apply_overrides() -> None:
        OrgCRUDL.actions += ('create',)
    #enddef on_apply_overrides

    class Create(SmartCreateView):
        title = _("Create Workspace")
        form_class = OrgCreateForm
        fields = ("first_name", "last_name", "email", "password", "name", "timezone", "credits")
        success_message = "Workspace successfully created."
        submit_button_name = _("Create")
        permission = "orgs.org_grant"
        success_url = "@orgs.org_create"
        default_template = 'orgs/org_create.html'
        exclude = ('created_by', 'modified_by', 'is_active')

        def has_object_permission(self, getter_name):
            # create views don't have an object, so this is always False
            return False

        def pre_save(self, obj):
            if self.request.user.id and self.request.user.id > 0:
                # auto populate created_by if it is present
                if hasattr(obj, 'created_by_id'):
                    obj.created_by = self.request.user

                # auto populate modified_by if it is present
                if hasattr(obj, 'modified_by_id'):
                    obj.modified_by = self.request.user

            return obj
        #enddef pre_save

        def derive_success_message(self):
            # First check whether a default message has been set
            if self.success_message is None:
                return _("Your new %s has been created.") % self.model._meta.verbose_name
            else:
                return self.success_message
        #enddef derive_success_message

        def derive_title(self):
            if not self.title:
                return _("Create %s") % force_str(self.model._meta.verbose_name).title()
            else:
                return self.title
        #enddef derive_title

        def create_user(self):
            user = User.objects.filter(username__iexact=self.form.cleaned_data["email"]).first()
            if not user:
                user = Org.create_user(self.form.cleaned_data["email"], self.form.cleaned_data["password"])

            user.first_name = self.form.cleaned_data["first_name"]
            user.last_name = self.form.cleaned_data["last_name"]
            user.save(update_fields=("first_name", "last_name"))
            return user
        #enddef create_user

        def get_form_kwargs(self):
            kwargs = super().get_form_kwargs()
            kwargs["branding"] = self.request.branding
            return kwargs
        #enddef get_form_kwargs

        def pre_save(self, obj):
            obj = super().pre_save(obj)

            self.user = self.create_user()

            obj.created_by = self.user
            obj.modified_by = self.user
            obj.brand = self.request.branding.get("brand", settings.DEFAULT_BRAND)
            obj.language = self.request.branding.get("language", settings.DEFAULT_LANGUAGE)
            obj.plan = self.request.branding.get("default_plan", settings.DEFAULT_PLAN)

            if obj.timezone.zone in pytz.country_timezones("US"):
                obj.date_format = Org.DATE_FORMAT_MONTH_FIRST

            # if we have a default UI language, use that as the default flow language too
            default_flow_language = languages.alpha2_to_alpha3(obj.language)
            obj.flow_languages = [default_flow_language] if default_flow_language else ["eng"]

            return obj

        def post_save(self, obj):
            obj = super().post_save(obj)
            obj.add_user(self.user, OrgRole.ADMINISTRATOR)

            if not self.request.user.is_anonymous and self.request.user.has_perm(
                    "orgs.org_grant"
            ):  # pragma: needs cover
                obj.add_user(self.request.user, OrgRole.ADMINISTRATOR)

            if self.form.cleaned_data["credits"] == settings.ORG_PLAN_ENGAGE:
                self.init_org(org=obj)
            else:
                obj.initialize(branding=obj.get_branding(), topup_size=self.form.cleaned_data["credits"])

            return obj
        #enddef post_save

        def init_org(self, org):
            """
            Initializes an organization, creating all the dependent objects we need for it to work properly.
            """
            from temba.middleware import BrandingMiddleware
            from temba.contacts.models import ContactField, ContactGroup

            org.is_multi_user = True
            org.is_multi_org = True
            org.plan = settings.ORG_PLAN_ENGAGE
            org.save(update_fields=("is_multi_user", "is_multi_org", 'plan'))
            with transaction.atomic():
                branding = org.get_branding()
                if not branding:
                    branding = BrandingMiddleware.get_branding_for_host("")
                #endif
                ContactGroup.create_system_groups(org)
                ContactField.create_system_fields(org)
            #endwith transaction

            # outside the transaction since it is going to call mailroom for flow validation
            org.create_sample_flows(branding.get("api_link", ""))
        #enddef init_org

    #endclass Create

#endclass OrgViewCreateMixin
