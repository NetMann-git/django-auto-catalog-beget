"""Ссылки удаления отдельных условий фильтра каталога."""

from django import template

register = template.Library()


@register.simple_tag(takes_context=True)
def catalog_without(context, *keys):
    """Сохранить остальные GET-параметры и сбросить страницу пагинации."""
    query = context["request"].GET.copy()
    for key in (*keys, "page"):
        query.pop(key, None)
    encoded = query.urlencode()
    return "?" + encoded if encoded else "?"
