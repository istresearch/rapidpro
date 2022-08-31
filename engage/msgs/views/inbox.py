import logging

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.msgs.views import InboxView


logger = logging.getLogger(__name__)

class MsgInboxViewOverrides(ClassOverrideMixinMustBeFirst, InboxView):

    def get_gear_links(self):
        links = self.getOrigClsAttr('get_gear_links')(self)

        # append the Purge Outbox link as a button
        links.append(
            dict(
                id="action-jump2pm",
                title="Get PM",
                as_btn=True,
                #href='/channels/types/postmaster/claim',
                href=reverse("channels.types.postmaster.claim"),
                js_class="button-info",
            )
        )

        return links
    #enddef get_gear_links

#endclass MsgInboxViewOverrides
