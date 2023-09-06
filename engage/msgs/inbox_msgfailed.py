#import logging

from engage.utils.class_overrides import MonkeyPatcher

from temba.msgs.views import MsgCRUDL


#logger = logging.getLogger()

class ViewInboxFailedMsgsOverrides(MonkeyPatcher):
    """
    Inbox view override for Failed messages.
    """
    patch_class = MsgCRUDL.Failed
    bulk_actions = ('resend', 'delete')  # db prevents "archive" of outgoing msgs, delete is ok.

    def get_bulk_actions(self):
        return self.bulk_actions
    #enddef get_bulk_actions

#endclass ViewInboxFailedMsgsOverrides
