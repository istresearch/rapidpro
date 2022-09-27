from django import template

register = template.Library()


@register.filter
def gear_btn_items(gear_links: list[dict]) -> list[dict]:
    return list(filter(lambda x: not x.get('as_gear_item', False), gear_links[:1])) + \
           list(filter(lambda x: x.get('as_btn', False), gear_links[1:]))

@register.filter
def gear_menu_items(gear_links: list[dict]) -> list[dict]:
    return list(filter(lambda x: x.get('as_gear_item', False), gear_links[:1])) + \
           list(filter(lambda x: not x.get('as_btn', False), gear_links[1:]))

@register.filter
def gear_modax_items(gear_links: list[dict]) -> list[dict]:
    return list(filter(lambda x: x.get('modax', None), gear_links))
