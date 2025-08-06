# stats_app/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter(name='replace')
def replace_string(value, arg):
    """
    Replaces all occurrences of a substring with another string.
    Usage: {{ value|replace:"old,new" }}
    """
    if isinstance(value, str) and ',' in arg:
        old, new = arg.split(',', 1)
        return value.replace(old, new)
    return value