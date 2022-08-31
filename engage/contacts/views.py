from engage.utils.class_overrides import ClassOverrideMixinMustBeFirst

from temba.contacts.views import ContactCRUDL

class ContactListOverrides(ClassOverrideMixinMustBeFirst, ContactCRUDL.List):

    def get_gear_links(self):
        links = self.getOrigClsAttr('get_gear_links')(self)

        # as_btn introduced to determine if placed in hamburger menu or as its own button
        el = [x for x in links if hasattr(x, 'id') and x.id == 'create-smartgroup']
        if el:
            el.title = "Save as Smart Group"
            el.modax = el.title
            el.as_btn = True
        #endif

        return links
    #enddef get_gear_links

#endclass ContactListOverrides
