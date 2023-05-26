from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst, ignoreDjangoModelAttrs

from temba.contacts.models import ContactField, Contact


class ContactFieldOverrides(ClassOverrideMixinMustBeFirst, ContactField):
    override_ignore = ignoreDjangoModelAttrs(ContactField)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    @classmethod
    def get_or_create(cls, org, user, key: str, name: str = None, value_type=None):
        try:
            return cls.getOrigClsAttr('get_or_create')(cls, org, user, key, name, value_type)
        except ValueError as ex:
            raise ValueError( str(ex).replace('campaigns', 'scenarios') )
        #endtry
    #enddef get_or_create

#endclass ContactFieldOverrides

class ContactOverrides(ClassOverrideMixinMustBeFirst, Contact):
    override_ignore = ignoreDjangoModelAttrs(Contact)

    # we do not want Django to perform any magic inheritance
    class Meta:
        abstract = True

    def get_urns(self):
        try:
            return self.getOrigClsAttr('get_urns')(self)
        except ValueError:
            return None
        #endtry
    #enddef get_urns

#endclass ContactOverrides
