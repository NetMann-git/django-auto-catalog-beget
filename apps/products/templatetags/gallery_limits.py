"""Expose shared upload bounds without duplicating values in JavaScript."""
from django import template
from apps.products.gallery_upload import limits

register = template.Library()


@register.simple_tag
def gallery_upload_limits() -> dict:
    return limits()
