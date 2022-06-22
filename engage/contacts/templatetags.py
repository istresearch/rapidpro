from temba.contacts.templatetags.contacts import URN_SCHEME_ICONS

def scheme_icon(scheme):
    return URN_SCHEME_ICONS.get(scheme, "")
