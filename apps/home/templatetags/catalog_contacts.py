"""Display the published home contact section on catalog pages."""

from django import template

from apps.home.models import ContactSettings

register = template.Library()


@register.inclusion_tag("home/sections/contacts.html")
def catalog_contacts() -> dict[str, ContactSettings | None]:
    """Reuse the same contact record as the home page."""
    return {
        "contact_settings": ContactSettings.objects.filter(
            pk=1, is_published=True
        ).first()
    }
