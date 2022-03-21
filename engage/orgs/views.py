from .assign_user import AssignUserMixin
from .postmaster import PostmasterChannelMixin
from .bandwidth import BandwidthChannelMixin

class EngageOrgCRUDMixin(BandwidthChannelMixin, PostmasterChannelMixin, AssignUserMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + (
            "bandwidth_connect",
            "bandwidth_international_connect",
            "bandwidth_account",
            "bandwidth_international_account",
            "postmaster_connect",
            "postmaster_account",
            "assign_user",
        )
        super().__init__(*args, **kwargs)
