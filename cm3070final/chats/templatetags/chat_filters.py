from django import template

register = template.Library()

# Custom template filter to fetch a dictionary key inside Django templates.
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, [])