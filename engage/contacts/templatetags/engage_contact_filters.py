from django import template

from temba.contacts.templatetags.contacts import URN_SCHEME_ICONS


register = template.Library()

@register.filter
def scheme_icon(scheme):
    return URN_SCHEME_ICONS.get(scheme, "")

@register.filter
def short_name(contact, org):
    return contact.get_display(org, short=True)

@register.filter
def history_user(user: dict) -> str:
    name = " ".join([user.get("first_name"), user.get("last_name")]).strip()
    if not name:
        name = user.get("email")
    return name
