#import logging

from engage.utils.class_overrides import MonkeyPatcher

from temba.msgs.views import MsgCRUDL


#logger = logging.getLogger()

class ViewMsgsOutboxOverrides(MonkeyPatcher):
    patch_class = MsgCRUDL.Outbox

    def get_gear_links(self):
        links = super(MsgCRUDL.Outbox, self).get_gear_links()

        # append the Purge Outbox link as a button
        links.append(
            dict(
                id="action-purge",
                title="Purge Outbox",
                as_btn=True,
                js_class="button-danger",
            )
        )

        return links
    #enddef get_gear_links

#endclass ViewInboxFailedMsgsOverrides
