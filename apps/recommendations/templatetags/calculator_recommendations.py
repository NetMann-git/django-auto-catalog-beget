"""Recommendations shared by the two car calculators."""
from django import template

from apps.recommendations.services import RecommendationService

register = template.Library()


@register.inclusion_tag(
    "recommendations/_calculator_recommended.html", takes_context=True,
)
def calculator_recommendations(context: template.Context) -> dict:
    """Reuse the existing selection rules and product card context."""
    result = context.flatten()
    result["recommended_products"] = RecommendationService.get_similar_products(
        [], page="calculators", limit=4,
    )
    return result
