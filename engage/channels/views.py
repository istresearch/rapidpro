from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin


class EngageChannelCRUDMixin(ManageChannelMixin, PurgeOutboxMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + \
            ManageChannelMixin.get_actions() + \
            PurgeOutboxMixin.get_actions()
        super().__init__(*args, **kwargs)
