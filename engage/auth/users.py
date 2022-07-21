from django.urls import reverse
from django.utils.translation import ugettext_lazy as _


class UserViewsUpdateMixin:

    def get_gear_links(self):
        return [
            dict(
                id="user-delete",
                title=_("Delete"),
                href=reverse("orgs.user_delete", args=[self.object.id]),
                goto_href=reverse("orgs.user_list"),
                as_btn=True,
                js_class="button-danger",
            )
        ]
    #enddef get_gear_links
#endclass UserViewsUpdateMixin
