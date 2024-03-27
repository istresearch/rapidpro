import logging
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartReadView

from engage.utils.middleware import RedirectTo

from temba.channels.models import Channel
from temba.orgs.views import OrgPermsMixin


class PmViewRead(OrgPermsMixin, SmartReadView):
    slug_url_kwarg = "uuid"
    fields = Channel._meta.get_fields()
    select_related = ("org",)
    title = _("PM Details")
    template_name = "pm/read.html"
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
        # if user has permission to the org, just switch the org for them
        obj_org = self.get_object().org
        self.logger.debug(f"user={user}", extra={
            'org': obj_org,
            'perm': self.permission,
            'my_args': args,
        })
        if obj_org.is_any_allowed(user, {'channels.channel_read', 'channels.channel_update'}):
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.get_object()
        context['page_title'] = self.title

        org = self.request.user.get_org()
        context['org'] = org

        context['apps'] = obj.config['apps'] if 'apps' in obj.config else ''

        context['device_name'] = obj.config['device_name']
        context['device_id'] = obj.config['device_id']

        #self.logger.debug("context=", extra={'context': context})
        return context
    #enddef get_context_data

#endclass Read
