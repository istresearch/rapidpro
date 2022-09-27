from collections import OrderedDict

from django import forms

from temba.orgs.views import OrgCRUDL

from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelFormAttrs
from temba.utils.fields import CheckboxWidget
from temba.utils.views import ComponentFormMixin


class ResthooksOverrides(ClassOverrideMixinMustBeFirst, ComponentFormMixin, OrgCRUDL.Resthooks):
    pass

class ResthookFormOverrides(ClassOverrideMixinMustBeFirst, OrgCRUDL.Resthooks.ResthookForm):
    override_ignore = ignoreDjangoModelFormAttrs(OrgCRUDL.Resthooks.ResthookForm)

    def add_remove_fields(self):
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
