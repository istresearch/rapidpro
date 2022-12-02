from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.contacts.models import ContactField


class ContactFieldOverrides(ClassOverrideMixinMustBeFirst, ContactField):
    override_ignore = ignoreDjangoModelAttrs(ContactField)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    @classmethod
    def get_or_create(cls, org, user, key, label=None, show_in_table=None, value_type=None, priority=None):
        try:
            return cls.getOrigClsAttr('get_or_create')(org, user, key, label, show_in_table, value_type, priority)
        except ValueError as ex:
            raise ValueError( str(ex).replace('campaigns', 'scenarios') )
        #endtry
    #enddef get_or_create

#endclass ContactFieldOverrides
