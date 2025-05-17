from django import template
from decimal import Decimal

register = template.Library()

@register.filter(name='mul')
def multiply(value, arg):
    """
    Multiply the arg and value together
    """
    try:
        # Convert to Decimal for more precise calculations
        return Decimal(str(value)) * Decimal(str(arg))
    except (ValueError, TypeError):
        # If inputs are not convertible to Decimal, return 0
        return 0

@register.filter(name='percentage')
def percentage(value, total):
    """
    Calculate percentage
    """
    try:
        if int(total) == 0:
            return 0
        return (Decimal(str(value)) / Decimal(str(total))) * 100
    except (ValueError, TypeError, ZeroDivisionError):
        return 0