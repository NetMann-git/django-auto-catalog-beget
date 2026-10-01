"""Public informational and legal pages."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_safe


@require_safe
def public_offer(request: HttpRequest) -> HttpResponse:
    """Show the draft until the service provider approves their actual terms."""
    response = render(request, 'home/legal/public_offer.html', {
        'page': {
            'title': 'Договор публичной оферты',
            'seo_title': 'Договор публичной оферты — Подберем АВТО',
            'search_description': 'Условия подбора и сопровождения приобретения автомобиля.',
        },
    })
    response['X-Robots-Tag'] = 'noindex, follow'
    return response
