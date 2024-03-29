import pytz
from django.conf import settings as siteconfig, settings
from django.contrib.auth.models import User
from django.db import transaction

from engage.utils.class_overrides import MonkeyPatcher

from temba.orgs.models import Org, OrgRole
from temba.utils import languages

# needed for legacy db migration
from django.contrib.auth.models import User as OldUser
from django.db import models


class OrgModelOverride(MonkeyPatcher):
    patch_class = Org

    def get_brand_domain(self):
        if siteconfig.ALT_CALLBACK_DOMAIN:
            return siteconfig.ALT_CALLBACK_DOMAIN
        else:
            return self.Org_get_brand_domain()
    #enddef get_brand_domain

    def release(self, user, **kwargs):
        with transaction.atomic():
            self.Org_release(user, **kwargs)
        #endwith
    #enddef release

    # ensure old definition exists, so we can migrate to new schema
    Org.administrators = models.ManyToManyField(OldUser, related_name='org_admins')
    Org.editors = models.ManyToManyField(OldUser, related_name='org_editors')
    Org.viewers = models.ManyToManyField(OldUser, related_name='org_viewers')
    Org.agents = models.ManyToManyField(OldUser, related_name='org_agents')
    Org.surveyors = models.ManyToManyField(OldUser, related_name='org_surveyors')

    def create_sub_org(self, name, timezone=None, created_by=None):
        if not self.is_multi_org:
            return
        #endif
        self.plan = settings.ORG_PLAN_ENGAGE
        if not timezone:
            timezone = self.timezone
        #endif
        if timezone.zone in pytz.country_timezones["US"]:
            date_format = Org.DATE_FORMAT_MONTH_FIRST
        else:
            date_format = self.date_format
        #endif
        # if we have a default UI language, use that as the default flow language too
        if self.language:
            default_flow_language = languages.alpha2_to_alpha3(self.language)
            self.flow_languages = [default_flow_language] if default_flow_language else ["eng"]
        else:
            self.language = "eng"
            self.flow_languages = ["eng"]
        #endif

        org = Org.objects.create(
            name=name,
            timezone=timezone,
            date_format=date_format,
            language=self.language,
            flow_languages=self.flow_languages,
            brand=self.brand,
            parent=self,
            slug=Org.get_unique_slug(name),
            created_by=created_by if created_by else self.created_by,
            modified_by=created_by if created_by else self.created_by,
            plan=self.plan,
            is_multi_user=self.is_multi_user,
            is_multi_org=True,
        )
        org.init_org(created_by)
        return org
    #enddef create_sub_org

    def init_org(self, created_by_id=None):
        """
        Initializes an organization, creating all the dependent objects we need for it to work properly.
        """
        from temba.middleware import BrandingMiddleware
        from temba.contacts.models import ContactField, ContactGroup

        if created_by_id is not None:
            self.add_user(created_by_id, OrgRole.ADMINISTRATOR)
        #endif

        self.is_multi_user = True
        self.is_multi_org = True
        self.plan = settings.ORG_PLAN_ENGAGE
        self.uses_topups = False

        self.save(update_fields=("is_multi_user", "is_multi_org", 'plan', 'uses_topups'))
        with transaction.atomic():
            branding = self.get_branding()
            if not branding:
                branding = BrandingMiddleware.get_branding_for_host("")
            #endif
            ContactGroup.create_system_groups(self)
            ContactField.create_system_fields(self)
        #endwith transaction

        # outside the transaction since it is going to call mailroom for flow validation
        self.create_sample_flows(branding.get("api_link", ""))
    #enddef init_org

    def is_any_allowed(self, user: User, perm_set: set) -> bool:
        role = self.get_user_role(user)
        return bool(perm_set & role.permissions) if role else False
    #enddef is_any_allowed

#endclass OrgModelOverride
