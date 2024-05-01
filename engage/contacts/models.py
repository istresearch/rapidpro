from django.conf import settings

from engage.utils.class_overrides import MonkeyPatcher

from temba.contacts.models import ContactField, Contact


class ContactFieldOverrides(MonkeyPatcher):
    patch_class = ContactField

    def get_or_create(cls: type[ContactField], org, user, key: str, name: str = None, value_type=None):
        try:
            return cls.ContactField_get_or_create(org, user, key, name, value_type)
        except ValueError as ex:
            raise ValueError( str(ex).replace('campaigns', 'scenarios') )
        #endtry
    #enddef get_or_create

#endclass ContactFieldOverrides

class ContactOverrides(MonkeyPatcher):
    patch_class = Contact

    def get_urns(self):
        try:
            return self.Contact_get_urns()
        except ValueError:
            return None
        #endtry
    #enddef get_urns

    @property
    def is_pm(self):
        return self.name.startswith(settings.SERVICE_CHANNEL_CONTACT_PREFIX) if self.name else False
    #enddef is_pm

    @property
    def channels(self):
        if not self.is_active:
            return []
        channels = {}
        for urn in self.urns.order_by("-priority", "pk").select_related("channel"):
            channels[urn.api_urn()] = {
                'uuid': urn.channel.uuid,
                'name': urn.channel.name,
                'address': urn.channel.address,
                'type': urn.channel.channel_type,
                'schemes': urn.channel.schemes,
                'urn': urn.api_urn(),
            }
        return channels
    #enddef channels

    def get_display(self, org=None, formatted=True):
        r = self.Contact_get_display(org, formatted)
        if r == r.strip():
            return r
        else:
            return r+"*"
    #enddef get_display

    def get_urn_display(self, org=None, scheme=None, formatted=True, international=False):
        r = self.Contact_get_urn_display(org, scheme, formatted, international)
        if r == r.strip():
            return r
        else:
            return r+"*"
    #enddef get_urn_display

#endclass ContactOverrides
