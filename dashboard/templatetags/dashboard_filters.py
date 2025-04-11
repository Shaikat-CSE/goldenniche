from django import template

register = template.Library()

@register.filter
def filter_by_id(value, arg):
    """
    Filter a list of objects by id
    Usage: {% with selected_object=objects|filter_by_id:object_id|first %}
    """
    try:
        # Convert arg to integer
        arg = int(arg)
        # Filter the queryset or list by id
        return [item for item in value if item.id == arg]
    except (ValueError, AttributeError):
        return []

@register.filter
def split(value, delimiter):
    """Split a string by delimiter and return a list"""
    return value.split(delimiter) 