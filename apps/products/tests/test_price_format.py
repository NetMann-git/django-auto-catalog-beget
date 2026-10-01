"""Price grouping must not depend on locale or lose fractional values."""
from decimal import Decimal

from django.template import Context, Template
from django.test import SimpleTestCase
from django.utils.translation import override

from apps.products.templatetags.price_format import price_format


class PriceFormatTests(SimpleTestCase):
    def test_prices(self):
        for raw, expected in (
            (1954369, '1\u00a0954\u00a0369'),
            (Decimal('1954369.00'), '1\u00a0954\u00a0369'),
            (Decimal('1234.50'), '1\u00a0234,5'),
            (0, '0'), (None, ''), ('∞', '∞'),
        ):
            with self.subTest(raw=raw):
                self.assertEqual(price_format(raw), expected)

    def test_template_locales(self):
        for language in ('en', 'ru'):
            with override(language):
                result = Template('{% load price_format %}{{ price|price_format }} ₽').render(
                    Context({'price': Decimal('1954369.00')}),
                )
                self.assertEqual(result, '1\u00a0954\u00a0369 ₽')
