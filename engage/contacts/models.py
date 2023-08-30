from engage.utils.class_overrides import MonkeyPatcher

from temba.contacts.models import ContactField, Contact


class ContactFieldOverrides(MonkeyPatcher):
    patch_class = ContactField

    def get_or_create(cls: type[ContactField], org, user, key: str, name: str = None, value_type=None):
        try:
            return cls.super_get_or_create(cls, org, user, key, name, value_type)
        except ValueError as ex:
            raise ValueError( str(ex).replace('campaigns', 'scenarios') )
        #endtry
    #enddef get_or_create

#endclass ContactFieldOverrides

class ContactOverrides(MonkeyPatcher):
    patch_class = Contact

    def get_urns(self):
        try:
            return self.super_get_urns()
        except ValueError:
            return None
        #endtry
    #enddef get_urns

#endclass ContactOverrides
