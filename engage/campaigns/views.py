from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import MonkeyPatcher

from smartmin.views import SmartUpdateView

from temba.campaigns.models import Campaign
from temba.campaigns.views import CampaignCRUDL
from temba.orgs.views import OrgFilterMixin, OrgPermsMixin


class CampaignCRUDLOverrides(MonkeyPatcher):
    patch_class = CampaignCRUDL

    class Delete(OrgFilterMixin, OrgPermsMixin, SmartUpdateView):
        fields = ()
        success_url = "uuid@campaigns.campaign_read"
        success_message = _("Scenario deleted")

        def save(self, obj):
            obj.apply_action_archive(self.request.user, Campaign.objects.filter(id=obj.id))
            return obj
    #endclass Delete


#endclass CampaignCRUDLOverrides

class CampaignArchivedOverrides(MonkeyPatcher):
    patch_class = CampaignCRUDL.Archived

    def on_apply_patches(self):
        self.bulk_actions += ("delete",)
    #enddef on_apply_patches

    def get_gear_links(self):
        links = self.super_get_gear_links()
        links.append(
            dict(
                title=_("Delete All"),
                style="btn-default",
                on_click="handleDeleteAll(event)",
                js_class="campaigns-btn-delete-all",
                href="#",
            )
        )
        return links
    #enddef get_gear_links

#endclass CampaignArchivedOverrides
