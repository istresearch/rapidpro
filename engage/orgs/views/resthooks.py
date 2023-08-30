from collections import OrderedDict

from django import forms

from temba.orgs.views import OrgCRUDL

from engage.utils.class_overrides import MonkeyPatcher
from temba.utils.fields import CheckboxWidget


class ResthookFormOverrides(MonkeyPatcher):
    patch_class = OrgCRUDL.Resthooks.ResthookForm

    def add_remove_fields(self: type(OrgCRUDL.Resthooks.ResthookForm)):
        resthooks = []
        field_mapping = []

        for resthook in self.instance.get_resthooks():
            check_field = forms.BooleanField(required=False, widget=CheckboxWidget())
            field_name = "resthook_%d" % resthook.id

            field_mapping.append((field_name, check_field))
            resthooks.append(dict(resthook=resthook, field=field_name))

        self.fields = OrderedDict(list(self.fields.items()) + field_mapping)
        return resthooks
    #enddef add_remove_fields

#endclass ResthookFormOverrides
