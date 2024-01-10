from engage.utils.class_overrides import MonkeyPatcher

from temba.campaigns.models import Campaign


class CampaignOverrides(MonkeyPatcher):
    patch_class = Campaign

    def apply_action_delete(cls, user, campaigns):
        for campaign in campaigns:
            campaign.delete()
        #endfor
    #enddef apply_action_delete

#endclass CampaignOverrides
