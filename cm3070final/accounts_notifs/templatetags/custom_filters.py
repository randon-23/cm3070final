from django import template

register = template.Library()

@register.filter
def pretty_title(value):
    return value.replace("_", " ").title()