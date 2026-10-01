"""Consistent readable prices, independent of the active locale."""

from decimal import Decimal, InvalidOperation
from typing import Any

from django import template

register = template.Library()


@register.filter
def price_format(value: Any) -> str:
    """Group thousands with nonbreaking spaces and preserve fractional prices."""
    if value is None or value == '':
        return ''
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return str(value)
    if not number.is_finite():
        return ''
    integer, dot, fraction = format(number, ',f').partition('.')
    integer = integer.replace(',', '\u00a0')
    fraction = fraction.rstrip('0')
    return integer + (',' + fraction if fraction else '')
