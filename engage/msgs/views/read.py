import logging
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartReadView

from engage.utils.middleware import RedirectTo
from temba.msgs.models import Msg

from temba.orgs.views import OrgPermsMixin


class Read(OrgPermsMixin, SmartReadView):
    """
    Choices are: attachments, broadcast, broadcast_id, channel, channel_id, channel_logs, contact, contact_id, contact_urn, contact_urn_id, created_on, direction, error_count, external_id, failed_reason, flow, flow_id, high_priority, id, labels, metadata, modified_on, msg_count, msg_type, next_attempt, org, org_id, queued_on, sent_on, status, text, topup, topup_id, uuid, visibility
    """
    slug_url_kwarg = "uuid"
    fields = ("text",)
    select_related = ("org", "contact", "current_flow",)
    title = _("Message Details")
    template_name = "msgs/msg_read.haml"
    logger = logging.getLogger()

    def get_gear_links(self):
        links = []
        #user = self.get_user()
        return links

    def has_permission(self, request: WSGIRequest, *args, **kwargs):
        user = self.get_user()
        # if user has permission to the org this contact resides, just switch the org for them
        obj_org = self.get_object().org
        self.logger.debug(f"user={user}", extra={
            'org': obj_org,
            'perm': self.permission,
            'my_args': args,
        })
        if obj_org.is_any_allowed(user, {'msgs.msg_read', 'msgs.msg_update'}):
            if obj_org.pk != user.get_org().pk:
                user.set_org(obj_org)
                request.session["org_id"] = obj_org.pk
                raise RedirectTo(request.build_absolute_uri())
            #endif
            return True
        else:
            return False
        #endif
    #enddef

#endclass Read
