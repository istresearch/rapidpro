import logging

from django.urls import reverse

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst
from engage.utils.strings import sanitize_text

from temba.msgs.views import InboxView


logger = logging.getLogger(__name__)

class MsgInboxViewOverrides(ClassOverrideMixinMustBeFirst, InboxView):
    """
    Sanitize the list of message contents to remove zero-width spaces and such.
    """

    """
    def pre_process(self, request, *args, **kwargs):
        self.getOrigClsAttr('pre_process')(self, request, *args, **kwargs)
        # give us the ability to override the pagination (super helpful in debugging)
        if 'r' in self.request.GET:
            self.refresh = self.request.GET['r']
        if 'nor' in self.request.GET:
            self.refresh = None
        if 'page_by' in self.request.GET:
            self.paginate_by = self.request.GET['page_by']
    """

    def _sanitizeMsgList(self, aList):
        """
        Ensure HTML in messages do not bork our display.
        :param aList: the list of message to process.
        :return: the processed list.
        """
        for theMsg in aList:
            if theMsg and hasattr(theMsg, 'text') and theMsg.text is not None:
                if isinstance(theMsg.text, str):
                    theMsg.text = sanitize_text(theMsg.text)
                elif isinstance(theMsg.text, dict):
                    for key, val in theMsg.text.items():
                        if isinstance(val, str):
                            theMsg.text[key] = sanitize_text(val)
                        #fi
                    #rof
                #fi
            #fi
        #rof
        return aList
    #enddef _sanitizeMsgList

    @staticmethod
    def on_apply_overrides(under_cls) -> None:
        ClassOverrideMixinMustBeFirst.setOrigMethod(under_cls, 'get_context_data')
        ClassOverrideMixinMustBeFirst.setOrigMethod(under_cls, 'get_gear_links')
    #enddef on_apply_overrides

    def get_context_data(self, **kwargs):
        org = self.request.user.get_org()
        if not org:
            from engage.utils.middleware import redirect_to
            redirect_to('/')
        #endif superuser
        context = self.orig_get_context_data(**kwargs)
        context['object_list'] = self._sanitizeMsgList(context['object_list'])
        return context
    #enddef get_context_data

    def get_gear_links(self):
        links = self.orig_get_gear_links()
        links.append(
            dict(
                title="Get PM",
                as_btn=True,
                href=reverse("channels.types.postmaster.claim"),
            )
        )
        return links
    #enddef get_gear_links

#endclass MsgInboxViewOverrides
