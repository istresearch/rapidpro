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
        BandwidthOrgModelOverrides.setClassOverrides()

        from .models import OrgModelOverride
        OrgModelOverride.setClassOverrides()

        from .views.user_assign import OrgViewAssignUserMixin
        OrgViewAssignUserMixin.setClassOverrides()

        from .views.user_delete import UserViewDeleteOverride
        UserViewDeleteOverride.setClassOverrides()

        from .views.user_list import OrgViewListUserOverrides
        OrgViewListUserOverrides.setClassOverrides()

        from .views.bandwidth import BandwidthChannelViewsMixin
        BandwidthChannelViewsMixin.setClassOverrides()

        from .views.home import HomeOverrides
        HomeOverrides.setClassOverrides()

        from .views.manage_orgs import AdminManageOverrides
        AdminManageOverrides.setClassOverrides()

        from .views.create import OrgViewCreateOverride
        OrgViewCreateOverride.setClassOverrides()

        from .views.resthooks import ResthookFormOverrides
        ResthookFormOverrides.setClassOverrides()
    #enddef ready

#endclass AppConfig
