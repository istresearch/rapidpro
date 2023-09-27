from django.apps import AppConfig as BaseAppConfig

class AppConfig(BaseAppConfig):
    """
    django app labels must be unique; so override AppConfig to ensure uniqueness
    """
    name = "engage.orgs"
    label = "engage_orgs"
    verbose_name = "Engage Orgs"

    def ready(self):
        from .bandwidth import BandwidthOrgModelOverrides
        BandwidthOrgModelOverrides.applyPatches()

        from .models import OrgModelOverride
        OrgModelOverride.applyPatches()

        from .views.user_assign import OrgViewAssignUserMixin
        OrgViewAssignUserMixin.applyPatches()

        from .views.user_delete import UserViewDeleteOverride
        UserViewDeleteOverride.applyPatches()

        from .views.user_list import OrgViewListUserOverrides
        OrgViewListUserOverrides.applyPatches()

        from .views.bandwidth import BandwidthChannelViewsMixin
        BandwidthChannelViewsMixin.applyPatches()

        from .views.home import HomeOverrides
        HomeOverrides.applyPatches()

        from .views.manage_orgs import AdminManageOverrides
        AdminManageOverrides.applyPatches()

        from .views.create import OrgViewCreateOverride
        OrgViewCreateOverride.applyPatches()

        from .views.resthooks import ResthookFormOverrides
        ResthookFormOverrides.applyPatches()

        from .views.sub_orgs import OrgViewSubOrgsOverrides
        OrgViewSubOrgsOverrides.applyPatches()

        from .views.join import JoinOverrides
        JoinOverrides.applyPatches()
    #enddef ready

#endclass AppConfig
