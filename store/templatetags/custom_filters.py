from django import template
from decimal import Decimal

register = template.Library()

@register.filter
def sub(value, arg):
    """Subtract the arg from the value."""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def mul(value, arg):
    """Multiply the value by the arg."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return value

@register.filter
def div(value, arg):
    """Divide the value by the arg."""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return value

@register.filter
def discount_percent(original_price, discount_price):
    """Calculate discount percentage."""
    try:
        original = float(original_price)
        discount = float(discount_price)
        if original > 0 and discount > 0 and original > discount:
            return int(((original - discount) / original) * 100)
        return 0
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def get_item(dictionary, key):
    """Get item from dictionary by key"""
    return dictionary.get(str(key), 0) 