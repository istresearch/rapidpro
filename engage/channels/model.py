from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin


class EngageChannelCRUDMixin(ManageChannelMixin, PurgeOutboxMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + (
            "manage",
            "purge_outbox",
        )
        super().__init__(*args, **kwargs)
