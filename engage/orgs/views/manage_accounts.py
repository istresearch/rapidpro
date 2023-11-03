from django.conf import settings

from engage.utils.class_overrides import MonkeyPatcher

from temba.orgs.views import OrgCRUDL

class OrgManageAccountsOverrides(MonkeyPatcher):
    patch_class = OrgCRUDL.ManageAccounts

    def get_context_data(self: type(OrgCRUDL.Manage), **kwargs):
        context = self.super_get_context_data(**kwargs)
        context["is_email_available"] = settings.SEND_EMAILS
        return context
    #enddef get_context_data

#endclass AdminManageMixin
