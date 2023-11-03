import logging
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartReadView

from engage.utils.middleware import RedirectTo
from engage.utils.strings import sanitize_text
from temba.api.v2.serializers import MsgReadSerializer

from temba.msgs.models import Msg
from temba.orgs.views import OrgPermsMixin


class Read(OrgPermsMixin, SmartReadView):
    """
    Choices are: attachments, broadcast, broadcast_id,
        channel, channel_id, channel_logs, contact, contact_id, contact_urn, contact_urn_id, reated_on,
        direction, error_count, external_id, failed_reason, flow, flow_id, high_priority, id, labels,
        metadata, modified_on, msg_count, msg_type, next_attempt, org, org_id, queued_on, sent_on, status,
        text, topup, topup_id, uuid, visibility
    """
    slug_url_kwarg = "uuid"
    fields = Msg._meta.get_fields()
    select_related = ("org", "contact", "current_flow",)
    title = _("Message Details")
    template_name = "msgs/msg_read.haml"
    show_channel_logs = True
    VISIBILITIES = {  # deleted messages should never be exposed over API
        Msg.VISIBILITY_VISIBLE: "visible",
        Msg.VISIBILITY_ARCHIVED: "archived",
        Msg.VISIBILITY_DELETED_BY_SENDER: "deleted by sender",
        Msg.VISIBILITY_DELETED_BY_USER: "deleted by user",
    }

    logger = logging.getLogger()

    def get_gear_links(self):
        links = []
        #user = self.get_user()
        return links
    #enddef get_gear_links

    def has_permission(self, request: WSGIRequest, *args, **kwargs):
        user = self.get_user()
        if user is AnonymousUser or user.is_anonymous:
            return False
        #endif is anon user
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

    def get_queryset(self, **kwargs):
        qs = super().get_queryset()
        if self.show_channel_logs:
            qs = qs.prefetch_related("channel_logs")
        return qs
    #enddef get_queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['page_title'] = self.title

        org = self.request.user.get_org()
        context["org"] = org

        if self.show_channel_logs:
            if obj.channel_logs:
                err_logs = sorted(obj.channel_logs.filter(is_error=True), key=lambda l: l.created_on, reverse=True)
                context["err_channel_logs"] = err_logs if err_logs and len(err_logs) > 0 else None
                msg_logs = sorted(obj.channel_logs.all(), key=lambda l: l.created_on, reverse=True)
                context["msg_channel_logs"] = msg_logs if msg_logs and len(msg_logs) > 0 else None
                context["show_channel_logs"] = msg_logs or err_logs
            else:
                context["msg_channel_logs"] = None
                context["show_channel_logs"] = False
        #endif

        msg_text = obj.text
        if msg_text:
            # Ensure HTML in messages does not bork our display.
            if isinstance(msg_text, str):
                msg_text = sanitize_text(msg_text)
            elif isinstance(msg_text, dict):
                for key, val in msg_text.items():
                    if isinstance(val, str):
                        msg_text[key] = sanitize_text(val)
                    #endif
                #endfor
            #endif
        #endif
        context["msg_text"] = msg_text

        msg_timestamps = [{
            'label': "Created:",
            'value': obj.created_on,
        }]
        if obj.queued_on:
            msg_timestamps.append({
                'label': "Queued:",
                'value': obj.queued_on,
            })
        #endif
        if obj.sent_on:
            msg_timestamps.append({
                'label': "Sent:",
                'value': obj.sent_on,
            })
        #endif
        if obj.modified_on and obj.modified_on != obj.created_on:
            msg_timestamps.append({
                'label': "Modified:",
                'value': obj.modified_on,
            })
        #endif
        if obj.next_attempt:
            msg_timestamps.append({
                'label': "Next attempt:",
                'value': obj.next_attempt,
            })
        #endif
        context['msg_timestamps'] = msg_timestamps
        context['msg_status'] = MsgReadSerializer.STATUSES.get(obj.status)
        context['msg_visibility'] = self.VISIBILITIES.get(obj.visibility)
        context['msg_type'] = MsgReadSerializer.TYPES.get(obj.msg_type)

        #self.logger.debug("context=", extra={'context': context})
        return context
    #enddef get_context_data

#endclass Read
