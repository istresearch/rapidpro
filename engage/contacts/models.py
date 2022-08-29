from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.contacts.models import ContactField

class ContactFieldOverrides(ClassOverrideMixinMustBeFirst, ContactField):
    override_ignore = ignoreDjangoModelAttrs(ContactField)

    @classmethod
    def get_or_create(cls, org, user, key, label=None, show_in_table=None, value_type=None, priority=None):
        try:
            cls.getOrigClsAttr(cls, 'get_or_create')(cls, org, user, key, label, show_in_table, value_type, priority)
        except ValueError as ex:
            raise ValueError( str(ex).replace('campaigns', 'scenarios') )
        #endtry
    #enddef get_or_create

#endclass ContactFieldOverrides
