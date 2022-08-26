from temba.msgs.views import MsgCRUDL

class ViewInboxFailedMsgsOverrides(MsgCRUDL.Failed):
    """
    Inbox view override for Failed messages.
    """
    bulk_actions = ('resend', 'delete')  # db prevents "archive" of outgoing msgs, delete is ok.

    def get_bulk_actions(self):
        return self.bulk_actions
    #enddef get_bulk_actions

#endclass ViewInboxFailedMsgsOverrides
