from smartmin.views import SmartCRUDL

from .view.list import PmViewList
from .view.read import PmViewRead

from temba.channels.models import Channel


class Postmaster(SmartCRUDL):
    actions = (
        "list",
        "read",
    )
    model = Channel
    app_name = 'PM'
    module_name = 'postmaster'
    path = 'pm'

    def permission_for_action(self, action):
        return "%s.%s_%s" % ('channels', self.model_name.lower(), action)
    #enddef permission_for_action
    def template_for_action(self, action):
        return "%s/%s_%s.html" % (self.app_name.lower(), self.module_name.lower(), action)
    #enddef template_for_action
    def url_name_for_action(self, action):
        return "%s.%s_%s" % (self.app_name.lower(), self.module_name.lower(), action)
    #enddef url_name_for_action

    class List(PmViewList):
        pass
    #endclass List

    class Read(PmViewRead):
        pass
    #endclass Read

#endclass Postmaster
