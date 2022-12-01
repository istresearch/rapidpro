import logging

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.msgs.views import MsgCRUDL, InboxView


logger = logging.getLogger(__name__)

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

    @classmethod
    def on_apply_overrides(cls) -> None:
        # child class wonky super() makes this workaround necessary
        setattr(cls, 'get_orig_context_data', getattr(InboxView, 'get_context_data'))
        logger.debug(f"override: set attr {str(cls)}.{'get_orig_context_data'} to {getattr(InboxView, 'get_context_data')}")
    #enddef on_apply_overrides

    def get_context_data(self, **kwargs):
        context = self.get_orig_context_data(**kwargs)
        context['object_list'] = self._sanitizeMsgList(context['object_list'])
        return context
    #enddef get_context_data

#endclass ViewInboxFailedMsgsOverrides
