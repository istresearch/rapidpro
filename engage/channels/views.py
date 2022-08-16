from .manage import ManageChannelMixin
from .purge_outbox import PurgeOutboxMixin
from .types.postmaster.apks import APIsForDownloadPostmaster


class EngageChannelCRUDMixin(ManageChannelMixin, PurgeOutboxMixin, APIsForDownloadPostmaster):
    def __init__(self, *args, **kwargs):
        self.actions = self.actions + \
            ManageChannelMixin.get_actions() + \
            PurgeOutboxMixin.get_actions() + \
            APIsForDownloadPostmaster.get_actions()
        super().__init__(*args, **kwargs)
