from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.middleware import RedirectTo

from temba.flows.views import FlowCRUDL


class FlowViewEditor(MonkeyPatcher):
    patch_class = FlowCRUDL.Editor

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

#endclass FlowViewEditor
