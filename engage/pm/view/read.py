import logging

from django.conf import settings
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest
from django.utils.http import urlencode
from django.utils.translation import gettext_lazy as _

from smartmin.views import SmartReadView

from engage.utils.middleware import RedirectTo

from temba.channels.models import Channel
from temba.orgs.views import OrgPermsMixin


class PmViewRead(OrgPermsMixin, SmartReadView):
    slug_url_kwarg = "uuid"
    fields = Channel._meta.get_fields() + ('children',)
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

        user = self.request.user
        org = user.get_org()
        context['org'] = org

        context['device_name'] = obj.name
        context['device_id'] = obj.address
        device_info = Channel.fetch_device_info(user, obj.address)
        context['device_info'] = device_info
        context['device_meta'] = device_info.get('meta', {})

        # app list versions sorted by chat mode
        if device_info['meta'] is not None:
            if device_info['meta']['extras'] is not None:
                chat_mode_apps = {}
                inactive_apps = {}
                for item in device_info['meta']['extras']['apps']:
                    chat_mode = item['modes'][0]
                    app = {
                        'chat_mode': chat_mode,
                        'app_version': item.get('version', 'unknown'),
                        'app_name': item.get('name', chat_mode),
                        'status': item.get('status', ''),
                    }
                    chat_mode_apps[chat_mode] = app
                    if not item.get('enabled', True):
                        inactive_apps[chat_mode] = app
                    #endif
                #endfor
                context['chat_mode_apps'] = chat_mode_apps
                context['inactive_apps'] = inactive_apps
            #endif
        #nedif

        if settings.LEAFLET_ENABLED:
            leafletConfig = {
                'id': 'road_map',
                'url': 'https://tiles.maps.elastic.co/v2/default/{z}/{x}/{y}.png',
                'urlparams': {
                    'elastic_tile_service_tos': 'agree',
                    'my_app_name': settings.DEFAULT_BRAND_OBJ['slug'],
                    'license': settings.LEAFLET_TOKEN,
                },
                'minZoom': 0,
                'maxZoom': 19,
                'attribution': '&copy; [OpenStreetMap](http://www.openstreetmap.org/copyright) contributors | [Elastic Maps Service](https://www.elastic.co/elasticmapsservice)',
            }
            leafletConfig['tileLayer'] = leafletConfig['url'] + '?' + urlencode(leafletConfig['urlparams'])

            context['leaflet_config'] = leafletConfig
        #endif

        #self.logger.debug("context=", extra={'context': context})
        return context
    #enddef get_context_data

#endclass Read
