from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin
from .types.postmaster.download import DownloadPostmasterMixin

class EngageChannelCRUDMixin(ManageChannelMixin, PurgeOutboxMixin, DownloadPostmasterMixin):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + \
            ManageChannelMixin.get_actions() + \
            PurgeOutboxMixin.get_actions() + \
            DownloadPostmasterMixin.get_actions()
        super().__init__(*args, **kwargs)
