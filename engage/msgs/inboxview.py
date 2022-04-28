from temba import settings
from temba.msgs.views import InboxView

class BaseInboxView(InboxView):
    """
    Base class for inbox views with message folders and labels listed by the side
    """
    def pre_process(self, request, *args, **kwargs):
        super().pre_process(request, *args, **kwargs)
        # give us the ability to override the pagination (super helpful in debugging)
        if settings.DEBUG:
            if 'r' in self.request.GET:
                self.refresh = self.request.GET['r']
            if 'nor' in self.request.GET:
                self.refresh = None
            if 'page_by' in self.request.GET:
                self.paginate_by = self.request.GET['page_by']

    def _sanitize_text(self, aText: str) -> str:
        """
        Ensure HTML in messages do not bork our display.
        :param aText: the text of a message to process.
        :return: the processed text.
        """
        #import engage.utils
        #engage.utils.var_dump(aText)
        if aText and aText is not None:
            # convert non-breaking spaces to normal spaces, ads abuse long strings of them
            aText = aText.replace(u'\xa0', ' ').replace('&nbsp;', ' ')
            # remove 0-width non-joiner characters near spaces
            aText = aText.replace(' '+u"\u200C", ' ').replace(' &zwnj;', ' ')
        return aText


    def process_list(self, aList):
        """
        Ensure HTML in messages do not bork our display.
        :param aList: the list of message to process.
        :return: the processed list.
        """
        for theMsg in aList:
            if theMsg and theMsg.text is not None:
                if isinstance(theMsg.text, str):
                    theMsg.text = self._sanitize_text(theMsg.text)
                elif isinstance(theMsg.text, dict):
                    for key, val in theMsg.text.items():
                        if isinstance(val, str):
                            theMsg.text[key] = self._sanitize_text(val)

        return aList

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.process_list(context['object_list'])
        return context
