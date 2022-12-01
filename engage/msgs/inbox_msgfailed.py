from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.msgs.views import MsgCRUDL, InboxView

class ViewInboxFailedMsgsOverrides(ClassOverrideMixinMustBeFirst, MsgCRUDL.Failed):
    """
    Inbox view override for Failed messages.
    """
    bulk_actions = ('resend', 'delete')  # db prevents "archive" of outgoing msgs, delete is ok.

    def get_bulk_actions(self):
        return self.bulk_actions
    #enddef get_bulk_actions

    # def get_context_data(self, **kwargs):
    #     import logging
    #     logger = logging.getLogger(__name__)
    #     logger.debug(str(MsgCRUDL.Failed) + "child of " + str(super(InboxView, self)))
    #     context = super(InboxView, self).get_context_data(**kwargs)
    #     context['object_list'] = self._sanitizeMsgList(context['object_list'])
    #     return context
    # #enddef get_context_data

#endclass ViewInboxFailedMsgsOverrides
