from temba import settings
import temba.msgs.views

OrigInboxView = temba.msgs.views.InboxView

class BaseInboxView(OrigInboxView):
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

    def process_list(self, aList):
        """
        Ensure HTML in messages do not bork our display.
        :param aList: the list of message to process.
        :return: the processed list.
        """
        for theMsg in aList:
            theText = theMsg['text']
            theText.replace(u'\xa0', ' ').replace('&nbsp;', ' ')
            theMsg['text'] = theText
        return aList

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = self.process_list(context['object_list'])
        return context
