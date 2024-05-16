from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest

from engage.channels.types.postmaster.schemes import PM_CHANNEL_MODES
from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.middleware import RedirectTo

from temba.flows.views import FlowCRUDL
from temba.utils import json


class FlowViewEditor(MonkeyPatcher):
    patch_class = FlowCRUDL.Editor

    def has_permission(self: FlowCRUDL.Editor, request: WSGIRequest, *args, **kwargs):
        result = super(FlowCRUDL.Editor, self).has_permission(request, *args, **kwargs)
        # if user has permission to the org, just switch the org for them
        if not result:
            user = self.get_user()
            if user is not AnonymousUser:
                obj_org = self.get_object().org
                if obj_org.pk != user.get_org().pk:
                    user.set_org(obj_org)
                    request.session["org_id"] = obj_org.pk
                    raise RedirectTo(request.build_absolute_uri())
                #endif
            #endif
        #endif
        return result
    #enddef has_permission

    def get_pm_schemes(self) -> list:
        # use str() to avoid "TypeError: Object of type __proxy__ is not JSON serializable"
        return [
            {
                "scheme": str(x.scheme),
                "name": str(x.urn_name),
                "path": str(x.label),
            } for mode, x in PM_CHANNEL_MODES.items()
        ]
    #enddef get_pm_schemes

    def get_context_data(self, *args, **kwargs):
        context = self.Editor_get_context_data(*args, **kwargs)
        context['pm_schemes'] = json.dumps(self.get_pm_schemes())
        return context
    #enddef get_context_data

    def get_gear_links(self):
        links = self.Editor_get_gear_links()
        links[0]['as_btn'] = True  # ensure first menu item stays a button as we pre-pend more.
        links.insert(0,
            dict(
                id="action-recenter",
                title="Re-center",
                style="button-default no-goto",
                as_btn=True,
                on_click='()=>{}',
            )
        )

        return links
    #enddef get_gear_links

#endclass FlowViewEditor
