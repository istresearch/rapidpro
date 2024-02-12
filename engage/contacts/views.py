from django.contrib.auth.models import AnonymousUser
from django.core.handlers.wsgi import WSGIRequest

from engage.utils.class_overrides import MonkeyPatcher
from engage.utils.middleware import RedirectTo

from temba.contacts.views import ContactCRUDL
from temba.utils.models import patch_queryset_count

class ContactListOverrides(MonkeyPatcher):
    patch_class = ContactCRUDL.List

    def get_bulk_actions(self: ContactCRUDL.List):
        return ("label", "block", "archive", "send") if self.has_org_perm("contacts.contact_update") else ()
    #enddef get_bulk_actions

    def get_gear_links(self):
        links = self.List_get_gear_links()

        # as_btn introduced to determine if placed in hamburger menu or as its own button
        el = [x for x in links if hasattr(x, 'id') and x.id == 'create-smartgroup']
        if el:
            el.title = "Save as Smart Group"
            el.modax = el.title
            el.as_btn = True
        #endif

        return links
    #enddef get_gear_links

    secondary_order_by = ["name"]

    def get_queryset(self: ContactCRUDL.List, **kwargs):
        search_query = self.request.GET.get("search", None)
        if search_query:
            return self.List_get_queryset(**kwargs)
        else:
            sort_on = self.request.GET.get("sort_on", None)
            if sort_on:
                self.sort_direction = "desc" if sort_on.startswith("-") else "asc"
                self.sort_field = sort_on.lstrip("-")
                sort_order = [sort_on]
            else:
                self.sort_direction = None
                self.sort_field = None
                sort_order = []
            #endif
            sort_order += self.secondary_order_by
            qs = self.group.contacts.filter(org=self.request.org).order_by(*sort_order).prefetch_related("org", "groups")
            patch_queryset_count(qs, self.group.get_member_count)
            return qs
        #endif search_query
    #enddef get_queryset

#endclass ContactListOverrides

class ContactReadOverrides(MonkeyPatcher):
    patch_class = ContactCRUDL.Read

    def has_org_perm(self: ContactCRUDL.Read, permission):
        obj_org = self.get_object_org()
        if obj_org:
            return self.get_user().has_org_perm(obj_org, permission)
        else:
            return self.Read_has_org_perm(permission)
        #endif
    #enddef

    def has_permission(self: ContactCRUDL.Read, request: WSGIRequest, *args, **kwargs):
        user = self.get_user()
        if user is AnonymousUser or user.is_anonymous:
            return False
        #endif is anon user
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

class ContactHistoryOverrides(MonkeyPatcher):
    patch_class = ContactCRUDL.History

    def as_json(self, context):
        """
        Don't reply back with the channel log or channel Django models on response. We use those custom fields on some Hamls, but
        we don't want it when this is JSON serialized. Things break.
        """
        events = []
        for e in context["events"]:
            e["channel_log"] = []
            e["channel"] = None
            events.append(e)

        return {
            "has_older": context["has_older"],
            "recent_only": context["recent_only"],
            "next_before": context["next_before"],
            "next_after": context["next_after"],
            "start_date": context["start_date"],
            "events": events,
        }
    #enddef

#endclass ContactHistoryOverrides
