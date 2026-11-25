"""Calculator recommendation integration checks."""
from unittest.mock import patch
from django.template import Context, Template
from django.template.loader import get_template
from django.test import SimpleTestCase
from apps.recommendations.forms import PromotedProductForm


class CalculatorRecommendationsTests(SimpleTestCase):
    def test_both_templates_compile(self):
        for page in ("utilization_fee", "customs_clearance"):
            get_template(f"calculator/{page}.html")

    def test_manager_can_select_calculators(self):
        self.assertIn(
            ("calculators", "Калькуляторы"),
            PromotedProductForm.base_fields["page"].choices,
        )

    @patch("apps.recommendations.templatetags.calculator_recommendations.RecommendationService.get_similar_products", return_value=[])
    def test_empty_recommendations_are_hidden(self, select):
        result = Template("{% load calculator_recommendations %}{% calculator_recommendations %}").render(Context({}))
        self.assertEqual(result.strip(), "")
        select.assert_called_once_with([], page="calculators", limit=4)
