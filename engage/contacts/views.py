from django.core.handlers.wsgi import WSGIRequest
from django.http import Http404

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst
from engage.utils.middleware import RedirectTo

from temba.contacts.views import ContactCRUDL

class ContactListOverrides(ClassOverrideMixinMustBeFirst, ContactCRUDL.List):

    def get_gear_links(self):
        links = self.getOrigClsAttr('get_gear_links')(self)

        # as_btn introduced to determine if placed in hamburger menu or as its own button
        el = [x for x in links if hasattr(x, 'id') and x.id == 'create-smartgroup']
        if el:
            el.title = "Save as Smart Group"
            el.modax = el.title
            el.as_btn = True
        #endif

        return links
    #enddef get_gear_links

#endclass ContactListOverrides

class ContactReadOverrides(ClassOverrideMixinMustBeFirst, ContactCRUDL.Read):

    def has_org_perm(self, permission):
        obj_org = self.get_object_org()
        if obj_org:
            return self.get_user().has_org_perm(obj_org, permission)
        else:
            return self.getOrigClsAttr('has_org_perm')(self, permission)
        #endif
    #enddef

    def has_permission(self, request: WSGIRequest, *args, **kwargs):
        user = self.get_user()
        # if user has permission to the org this contact resides, just switch the org for them
        obj_org = self.get_object_org()
        if user.has_org_perm(obj_org, self.permission):
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

#endclass ContactReadOverrides
