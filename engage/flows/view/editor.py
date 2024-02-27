import logging
from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.middleware import RedirectTo

from temba.flows.views import FlowCRUDL


class FlowViewEditor(MonkeyPatcher):
    patch_class = FlowCRUDL.Editor

    def has_permission(self: FlowCRUDL.Editor, request: WSGIRequest, *args, **kwargs):
        result = super(FlowCRUDL.Editor, self).has_permission(request, *args, **kwargs)
        # if user has permission to the org, just switch the org for them
        if not result:
            user = self.get_user()
            obj_org = self.get_object().org
            if obj_org.pk != user.get_org().pk:
                user.set_org(obj_org)
                request.session["org_id"] = obj_org.pk
                raise RedirectTo(request.build_absolute_uri())
            #endif
        #endif
        return result
    #enddef has_permission

#endclass FlowViewEditor
