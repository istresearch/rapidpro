from .assign_user import AssignUserMixin
from .bandwidth import BandwidthChannelMixin
from .postmaster import PostmasterChannelMixin

class EngageOrgCRUDMixin(BandwidthChannelMixin, PostmasterChannelMixin, AssignUserMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + \
            AssignUserMixin.get_actions() + \
            BandwidthChannelMixin.get_actions() + \
            PostmasterChannelMixin.get_actions()
        super().__init__(*args, **kwargs)
