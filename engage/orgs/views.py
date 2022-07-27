from .assign_user import AssignUserMixin
from .bandwidth import BandwidthChannelViewsMixin

class EngageOrgCRUDMixin(BandwidthChannelViewsMixin, AssignUserMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + \
            AssignUserMixin.get_actions() + \
            BandwidthChannelViewsMixin.get_actions()
        super().__init__(*args, **kwargs)
