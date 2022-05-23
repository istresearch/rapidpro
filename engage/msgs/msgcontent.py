from engage.utils.strings import sanitize_text

class ListMsgContentMixin:
    """
    Sanitize the list of message contents to remove zero-width spaces and such.
    """

    """
    def pre_process(self, request, *args, **kwargs):
        super(ListMsgContentMixin, self).pre_process(request, *args, **kwargs)
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
            if theMsg and theMsg.text is not None:
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

    def get_context_data(self, **kwargs):
        context = super(ListMsgContentMixin, self).get_context_data(**kwargs)
        context['object_list'] = self._sanitizeMsgList(context['object_list'])
        return context
