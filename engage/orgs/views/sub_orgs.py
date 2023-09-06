from html import escape as html_escape

from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from temba.orgs.views import OrgCRUDL

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.logs import LogExtrasMixin


class OrgViewSubOrgsOverrides(MonkeyPatcher, LogExtrasMixin):
    patch_class = OrgCRUDL.SubOrgs

    def get_gear_links(self):
        links = []
        #call original overridden function, not super(), so we don't have to re-write it here.
        links.extend(self.super_get_gear_links())

        theUrl4OrgDashboard = reverse("dashboard.dashboard_home")
        theUrl4AddOrg = reverse("orgs.org_create_sub_org")
        for item in links:
            if item['href'] == theUrl4OrgDashboard:
                item['js_class'] = "button-primary"
            #endif
            if item['href'] == theUrl4AddOrg:
                item['as_btn'] = True
            #endif
        #endfor each link item

        return links
    #enddef get_gear_links

    def get_name(self, obj):
        org_type = "child"
        if not obj.parent:
            org_type = "parent"
        if self.has_org_perm("orgs.org_create_sub_org") and obj.parent and obj != self.get_object():
            return mark_safe(f"""
                <temba-modax header={_('Update')} endpoint={reverse('orgs.org_edit_sub_org')}?org={obj.id}>
                    <div class='{org_type}-org-name linked'>{html_escape(obj.name)}</div>
                    <div class='org-timezone'>{obj.timezone}</div>
                </temba-modax>
            """)
        else:
            return mark_safe(f"""
                <div class='org-name'>{html_escape(obj.name)}</div>
                <div class='org-timezone'>{obj.timezone}</div>
            """)
        #endif
    #enddef get_name

    def get_manage(self, obj):  # pragma: needs cover
        if obj == self.get_object():
            return mark_safe(
                f'<a href="{reverse("orgs.org_manage_accounts")}" class="float-right pr-4"><div class="button-light inline-block ">{_("Manage Logins")}</div></a>'
            )
        elif obj.parent:
            return mark_safe(
                f'<a href="{reverse("orgs.org_manage_accounts_sub_org")}?org={obj.id}" class="float-right pr-4"><div class="button-light inline-block">{_("Manage Logins")}</div></a>'
            )
        else:
            return ""
        #endif
    #enddef get_manage

#endclass OrgViewSubOrgsOverrides
