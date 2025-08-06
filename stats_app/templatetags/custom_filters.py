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

@register.filter
def humanize_number(value):
    """
    Converts a large number into a human-readable format (e.g., 1000000 -> 1M).
    """
    try:
        value = int(value)
    except (ValueError, TypeError):
        return value

    if value >= 1_000_000_000_000:
        return f"{value / 1_000_000_000_000:.1f}T"
    elif value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.1f}B"
    elif value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    elif value >= 1000:
        return f"{value / 1000:.1f}K"
    else:
        return value